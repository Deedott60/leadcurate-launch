---
name: leadcurate
description: LeadCurate source of truth — current state, 4-tier product system, brand voice rules, customer flow, agent roles. Read first whenever any task mentions LeadCurate, intake form, quotes, audits, tiers, county data, wholesaling, REI lead lists, or motivated seller data.
metadata:
  type: project
  version: 2026-06-25-v2
  owner: Derrick McDonald (dmcdonald5649@gmail.com)
  source: synced from github.com/Deedott60/leadcurate-launch/CLAUDE.md
---

# LeadCurate — Source of Truth

> **This file is the single source of truth for every LeadCurate task.**
> Maintained by Claude (orchestrator) and synced from the canonical `/CLAUDE.md` at the repo root.

---

## 1. What LeadCurate is

LeadCurate sells **curated motivated-seller property data** to real-estate wholesalers, fix-and-flip investors, and buy-and-hold landlords. The product is filtered, scored, source-attributed county records — not raw dumps.

**Differentiators:** velocity scoring (when motivation peaks, not just whether distress exists), capped buyer access per market (1–3 seats so records stay warm), branded delivery.

**Direct competitors:** PropStream, BatchLeads, ListSource, DealMachine, PropertyRadar.

**Operator:** Derrick McDonald (NOT Daniel, NOT Derek, NOT Ella). Solo. LeadCurate LLC, registered in NC, Mecklenburg County.

---

## 2. Current state (as of 2026-06-25)

### Inventory
- **22 counties pulled** across 12 states
- **~80 million raw records** on VPS (verified by direct count, NOT the older "14.2M" number)
- **9.2 GB** total raw data
- **9 markets sellable today** (processed, scored, packaged)
- **13 markets in processing**

### Sellable markets ready today
Wake NC (10,472), Cobb GA (5,678), Guilford NC (5,000), Marion IN (5,000), DeKalb GA (5,000), Forsyth NC (5,000), Fulton GA (5,000), Harris TX Permit Burnout (1,500), Jefferson AL (21).

### What's live
- Intake form: `https://deedott60.github.io/leadcurate-launch/intake/`
- Packages overview (customer-facing, NO pricing): `https://deedott60.github.io/leadcurate-launch/packages/`
- Quote builder: `https://deedott60.github.io/leadcurate-launch/quote-template/?buyer=X&market=Y&tier=Z`
- Tier reference (internal): `https://deedott60.github.io/leadcurate-launch/tiers/`
- Operator dashboard: `https://deedott60.github.io/leadcurate-launch/command/`
- Supabase project `jdmlsraqioigbukspduo` — 16 tables, RLS enabled
- Hostinger one-click n8n install in progress (initiated 2026-06-25)

### What's PARKED
- `/site/` landing page — Phase 3 work, don't touch
- Pricing changes — Derrick decides
- Production tables — never insert test data

---

## 3. The 4-Tier Product System (LOCKED 2026-06-23)

Customer NEVER sees "Tier 1/2/3/4" labels — internal only. They see one tier (the one we recommended based on their intake) with the brand tier name.

### Tier 1 — Imminent Auction Hot Sheet
- **Price:** $397 launch (first 5 buyers) → $497 standard
- **Cadence:** One-time per sheet (NOT subscription — auctions are episodic)
- **Trigger:** verified auction date in next 30 days, score forced 95-100
- **Buyer:** fast-moving wholesalers

### Tier 2 — Fresh Triggers Feed
- **Price:** $197/week launch → $297/week standard
- **Cadence:** Weekly subscription (only recurring tier)
- **Trigger:** new court filing or code violation in last 7 days, score forced 92
- **Buyer:** daily cold callers

### Tier 3 — The Breaking Point
- **Price:** $249 one-time, monthly refresh option
- **Trigger:** debt > 5% of property value OR debt growing YoY (tax OR municipal)
- **Buyer:** buy-and-hold + flippers

### Tier 4 — Curated Distress List
- **Price:** $99 first 5 buyers → $149 standard, monthly refresh option
- **Trigger:** standard source filter (Tax Delinquent, Absentee, Probate, High Equity)
- **Buyer:** everyone — foundational entry product

---

## 4. Brand voice (LOCKED — never violate)

**Position:** Premium. PropStream is the cheap recycled-list option. LeadCurate is curated, scored, limited-access.

### BANNED in customer-facing copy
"cheap" / "cheaper" / "affordable" / "save" / "savings" / "save money" / "less you pay" / "won't pay for" / "starting at just $X" / "value pricing" / any "you'll spend less" angle.

### REQUIRED framing
Fit, quality, accuracy, freshness, urgency, exclusivity. Match customers to the *right* tier — not the *cheapest*. Never apologize for price.

### Do/don't pairs
- ❌ "less you pay for stuff you won't use" → ✅ "the sharper we can match you to the tier that fits"
- ❌ "starting at just $149" → ✅ "entry tier: $149 — built for your first list"
- ❌ "free game / enough game to work the batch" → ✅ "practical training most sellers leave out"
- ❌ "guaranteed motivated sellers" → ✅ "scored for motivation density, you still handle outreach"
- ❌ "Reply YES" → ✅ "Confirm selection →"
- ❌ Quote with A/B/C menu → ✅ Single recommended tier, single Confirm button

---

## 5. Customer flow (manual Phase 1)

1. Prospect fills intake → `intake_requests` row → trigger creates `prospects` row → Derrick sees in dashboard
2. Operator reads intake, decides tier from urgency + role + volume signals
3. Operator uses dashboard "Send a quote" → fills name + market + tier → Build → personalized URL
4. Operator sends URL → prospect sees ONE offer with Confirm button
5. Prospect confirms with name + phone → email to Derrick
6. Operator sends payment (Cash App / Zelle / Stripe)
7. Branded XLSX delivered within 24h

### Tier picker logic
| Intake says... | Recommend |
|---|---|
| Urgency "Need it now (24-48h)" or "This week" | Tier 1 Hot Sheet |
| Role "Acquisitions team" + "Cold call every day" | Tier 2 Fresh Triggers |
| Volume "500-1500" + high-quality preference | Tier 3 Breaking Point |
| First time / exploring / general | Tier 4 Curated Distress List |

---

## 6. Visual brand kit

- **Colors:** emerald #15803d · cream #faf7f2 · dark #0f172a · slate #475569 · line #e2dccf
- **Per-tier accents:** crimson #991b1b (T1) · gold #b45309 (T2) · emerald (T3) · blue #1d4ed8 (T4)
- **Fonts:** Inter (body) · Playfair Display (display)
- **Component patterns:** see existing audit/packages/quote/tiers/intake pages — match them, never invent

### Reference files in the repo (READ before building any artifact)
| Building... | Read this |
|---|---|
| Intake form | `docs/intake/index.html` |
| Quote / pricing page | `docs/quote-template/index.html` |
| Customer-facing packages overview | `docs/packages/index.html` |
| Internal tier reference | `docs/tiers/index.html` |
| Analytical audit / data report | `docs/system-audit/index.html`, `docs/property-numbers/index.html` |
| Operator dashboard | `docs/command/index.html` |
| Outreach message templates | `docs/OUTREACH-PLAYBOOK.md` |

---

## 7. Agent roles

| Agent | Role |
|---|---|
| **Claude (orchestrator)** | Strategy, code, brand, sync this file |
| **Codex** | VPS infrastructure, security, scrapers — reads `docs/CURRENT-HANDOFF.md` (not dated handoff files, those are archived) |
| **Hermes (Danny)** | 24/7 ops — runs scrapers, monitors Conference Room, executes activity_feed tasks |
| **Derrick** | Business decisions, pricing, sales |

### Conference Room protocol
```sql
INSERT INTO activity_feed (event_type, source, title, body, target)
VALUES ('conf:role', 'hermes', '<task>', '<body>', '<target>');
```
Targets: claude | codex | hermes | derrick | all
Event types: conf:role | conf:done | conf:status | conf:blocker | conf:urgent

---

## 8. Current handoff — single source of truth

`docs/CURRENT-HANDOFF.md`. This file is edited in place, not recreated — always current, never a stale date to guess at. Read it every session alongside `docs/AGENT-OPERATING-RULES.md`. Dated `docs/codex-handoff-*.md` files are archived in `docs/codex-handoff-archive/` for history only; don't treat them as active.

---

## 9. Campaigns (next phase)

Pending: Facebook account credentials, X account credentials, domain email, audience pool definition. Don't post for campaigns without Derrick's explicit go.

---

## 10. What Hermes specifically helps with for LeadCurate

1. Pulling fresh data from county sources — see `leadcurate-county-data-pull` skill
2. Running snapshot processors — pattern: process raw → normalize → score → tier-classify → write CSV + meta.json
3. Running the tier classifier on a market: `python3 /opt/leadcurate/scripts/tier_classifier.py <snapshot.csv>`
4. Watching for new intake submissions and pinging Claude with priority info
5. Building branded delivery XLSX packages for paid orders

---

## 11. Don't do

- Never insert test data into prospects, leads, intake_requests, messages
- Never touch `/site/` landing page without Derrick's approval
- Never change pricing or make business decisions
- Never use "Daniel" or "Derek" — name is Derrick
- Never apologize for price in customer copy
- Never tell Derrick a system is "broken" without SSH-verifying current state first

---

## 12. Stale info to overwrite

| Old | Reality |
|---|---|
| "14.2M records" | ~80M raw |
| "Hermes brain offline" | Working with OpenAI + Gemini keys |
| "$175 deposit / $497mo seat" pricing | Dead — 4-tier system above |
| "A/B/C quote menu" | Single tier per quote |
| Operator "Daniel" | Derrick |
| "Ella orchestrator" | Claude |
| "Nginx preview at 76.13.25.117/leadcurate-preview/" | Live on GitHub Pages |
| "Hermes installs n8n via Docker" | Hostinger one-click |

---

## Change log

- **2026-06-25** — Synced to v2 from `/CLAUDE.md`. Added campaigns section, decisions log reference, Lead Scout status flag, lessons. Replaces 2026-06-25-v1.
