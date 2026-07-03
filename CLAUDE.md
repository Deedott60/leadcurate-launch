# 🟢 LEADCURATE PROJECT — Master File 🟢
# (Filename is CLAUDE.md because of Claude Code's auto-load convention. This file ONLY applies to the LeadCurate project.)

> **Scope: LeadCurate ONLY.** For universal Claude operating rules that apply to every project, see `C:\Users\lenovo\.claude\CLAUDE.md` and `C:\Users\lenovo\.claude\rules\*.md` — including `verification-discipline.md`.
>
> This file is loaded automatically when working in this repo. It is the single source of truth for every agent (Claude, Codex, Hermes) working on LeadCurate.
>
> Owner: Derrick McDonald · Repo: github.com/Deedott60/leadcurate-launch · Maintained by Claude (orchestrator)
>
> **Need a quick reference of all files + how to use them? See `LEADCURATE-CHEAT-SHEET.md` in this same folder.**

---

## 0. Session startup (every new Claude session in this repo)

1. **Check the Conference Room** — query Supabase via MCP:
   ```sql
   SELECT id, source, title, body, target, created_at
   FROM activity_feed
   WHERE target IN ('claude','all') AND event_type LIKE 'conf:%'
   ORDER BY created_at DESC LIMIT 10;
   ```
   Act on anything addressed to Claude. Forward tasks for other agents accordingly.
2. **Post a status:**
   ```sql
   INSERT INTO activity_feed (event_type, source, title, target)
   VALUES ('conf:status', 'claude', 'Claude online — checked Conference Room', 'all');
   ```
3. Then respond to whatever Derrick said in chat.

---

## 1. What LeadCurate is

LeadCurate sells **curated motivated-seller property data** to real-estate wholesalers, fix-and-flip investors, and buy-and-hold landlords. The product is filtered, scored, source-attributed county records — not raw dumps.

**Differentiators:** velocity scoring (when motivation peaks, not just whether distress exists), capped buyer access per market (1–3 seats so records stay warm), branded delivery.

**Direct competitors:** PropStream, BatchLeads, ListSource, DealMachine, PropertyRadar.

**Operator:** Derrick McDonald (NOT Daniel, NOT Derek, NOT Ella). Solo. LeadCurate LLC, registered in NC, Mecklenburg County.

---

## 2. Current state (as of 2026-06-27)

### Inventory
- **22 counties pulled** across 12 states
- **~80 million raw records** on VPS (verified by direct count, NOT the older "14.2M" number)
- **9.2 GB** total raw data
- **9 markets sellable today** (processed, scored, packaged)
- **13 markets in processing**

### Sellable markets ready today
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

### What's live
- Intake form: `https://deedott60.github.io/leadcurate-launch/intake/`
- Packages overview (customer-facing, NO pricing): `https://deedott60.github.io/leadcurate-launch/packages/`
- Quote builder (in dashboard, generates personalized URLs): `https://deedott60.github.io/leadcurate-launch/quote-template/?buyer=X&market=Y&tier=Z`
- Tier reference (internal only): `https://deedott60.github.io/leadcurate-launch/tiers/`
- Operator dashboard: `https://deedott60.github.io/leadcurate-launch/command/`
- Supabase project `jdmlsraqioigbukspduo` — 16 tables, RLS enabled, auto-pipeline trigger on intake_requests → prospects
- Hermes (Danny) running on VPS at 76.13.25.117, brain v0.15.1 with OpenAI + Gemini keys
- **n8n LIVE** at `http://76.13.25.117:32768` (Hostinger one-click, Derrick owns the login). API key stored on VPS `/opt/leadcurate/.env`. API verified 200. No workflows built yet — wiring only. ⚠️ http + Docker-assigned port; needs TLS + pinned port before real customer data flows.
- **VPS crontab (verified 2026-06-27):** `*/5` conference-watcher + `15 2 * * 0` auction scrapers. That's ALL. (See §13 — Lead Scout is NOT scheduled.)
- **Customers table:** 0 (a leftover RLS-test row was removed 2026-06-27; no real customers yet)
- **SSH from Derrick's Windows box:** restored 2026-06-27 (a UTF-8 BOM in `~/.ssh/config` had broken all ssh; stripped, backup saved)

### Credentials location (so we never re-ask Derrick)
**All LeadCurate secrets live in VPS `/opt/leadcurate/.env` (chmod 600, NOT in the repo).** Read them from there via SSH — never ask Derrick to paste again. Currently stored: `N8N_URL`, `N8N_API_KEY`, `LEADCURATE_DOMAIN`, `LEADCURATE_FROM_EMAIL`, `HOSTINGER_API_KEY` (for DNS/domain automation). Mailbox password is NOT stored (secret, not needed in files). To list names: `ssh leadcurate-vps "grep -oE '^[A-Za-z0-9_]+=' /opt/leadcurate/.env"`.

### Domain + email (LIVE 2026-06-27)
- **Domain:** `leadcurate.com` (Hostinger). **Business email:** `hello@leadcurate.com`.
- Unblocks: domain-swap procedure (§10) + autoresponder FROM address (still needs RESEND_API_KEY or SMTP creds to actually send).

### What's PARKED (do not touch without Derrick's go)
- `/site/` landing page — Phase 3 work
- Pricing changes — Derrick decides
- Production tables — never insert test data

---

## 3. The 5-Tier Product System (LOCKED 2026-06-29 — supersedes 2026-06-23 version)

Customer NEVER sees "Tier 1/2/3/4/5" labels — that's internal. They see ONE tier (the one we recommended based on their intake) with a brand label that adapts to the lane they chose.

**Why this got restructured (2026-06-29):** the prior version buried **Probate** in Tier 4 (foundational entry), but the market sells probate as a *premium* product (All The Leads $249–$1,099/mo, US Lead List $1.60/lead). The prior version also had no list sizes per tier, which let "5,000 records at $149" pricing slip in — that's bulk-aggregator math ($0.03/lead) wearing a premium tuxedo. Fixed both.

**List size discipline:** every SKU has a target record count. Per-lead cost must land in the premium range ($0.30–$1.99/lead). NEVER ship 5,000 records at $149 again.

### Tier 1 — Entry / Foundation List
- **Customer-facing brand label** (adapts to their picked lane):
  - "Curated Distress List" (default / multi-foundational)
  - "Active Homeowner List" (Individual/homeowner lane)
  - "Absentee Owner List" (Absentee lane)
  - "High-Equity Owners List" (High-equity lane)
  - "Liens Watchlist" (Liens lane)
- **Price:** $149 launch (first 5 buyers) → $249 standard
- **Records:** 500, hand-scored
- **Per-lead:** $0.30 launch / $0.50 standard
- **Cadence:** one-time with optional $99 monthly refresh add-on
- **Lanes eligible:** ONLY foundational/mid-premium — Tax Delinquent, Absentee, High Equity, Individual/homeowner, Liens, Entity-owned, Vacant land
- **Buyer:** foundational entry — anyone testing the product
- **Phase 3 subscription price:** $150/month

### Tier 2 — Targeted Premium (court-scrape specialty)
- **Customer-facing brand label** (adapts to lane):
  - "Probate Premium" (Probate / inherited lane)
  - "Pre-Foreclosure Premium" (Pre-Foreclosure NOD lane, non-auction)
  - "Code Violations List" (Code Violations lane)
  - "Active Permits Distress" (Active permits / damage lane)
  - "The Breaking Point" (computed debt-growing — debt > 5% property value OR debt growing YoY)
- **Price:** $249 launch (first 5 buyers) → $397 standard
- **Records:** 250–500, hand-scored
- **Per-lead:** $0.50–$1.00 launch
- **Cadence:** one-time with optional $99 monthly refresh add-on
- **Lanes eligible:** ONLY court-scrape premium — Probate, Pre-Foreclosure, Code Violations, Active Permits, or computed debt-growing
- **Buyer:** targeted operators who know the signal they want
- **Phase 3 subscription price:** $250/month
- **Why this tier exists:** the direct competitor segment (All The Leads, Foreclosures Daily, ProbateData) sells exactly this — single specialty lane, monthly drops. Our launch price ($249 one-time, 500 records) ≈ All The Leads entry month ($249).

### Tier 3 — Imminent Auction Hot Sheet
- **Customer-facing brand:** "Imminent Auction Hot Sheet"
- **Price:** $397 launch (first 5 buyers) → $497 standard
- **Records:** 250 (scarce by nature — verified auctions in next 30 days)
- **Per-lead:** $1.59 launch / $1.99 standard
- **Cadence:** one-time per sheet (NOT subscription — auctions are episodic)
- **Trigger:** verified auction date in next 30 days, score forced 95–100
- **Buyer:** fast-moving wholesalers who can contract this week
- **Phase 3 subscription price:** $500/month for guaranteed monthly drop when auctions exist in their market

### Tier 4 — Market Dominance (All-Lanes Bundle)
- **Customer-facing brand:** "Market Dominance"
- **Price:** $697 launch (first 5 buyers) → $797 standard
- **Records:** 1,000 — top-scored across ALL 8 lanes, deduplicated
- **Per-lead:** $0.70 launch / $0.80 standard
- **Cadence:** one-time with optional $149/month refresh add-on
- **Lanes:** ALL 8 (Tax Delinquent, Probate, Code Violations, Pre-Foreclosure, Active Permits, Owner Records, High Equity, Absentee) — scored together
- **Buyer:** acquisitions teams wanting every distress signal in their market
- **Phase 3 subscription price:** $700/month

### Tier 5 — Exclusive Territory
- **Customer-facing brand:** "Exclusive Territory"
- **Price:** $1,497 launch / $1,997 standard
- **Records:** 1,000 across all 8 lanes — capped to 1 buyer per market (NO ONE else gets this market while subscription active)
- **Per-lead:** $1.50 launch / $2.00 standard
- **Cadence:** one-time, OR monthly with continuous exclusivity guarantee
- **Buyer:** enterprise wholesalers / funds wanting to lock a metro
- **Phase 3 subscription price:** $1,500/month (with auto-renewal lock on territory)
- **3× multiplier** over Tier 4 reflects exclusivity premium (US Lead List sells the 3-buyer-per-county model — we're going to 1-buyer-per-market for top end).

### Tier picker logic — operator routes from intake
| Intake says... | Recommend |
|---|---|
| Lane = Probate/Pre-Foreclosure/Code Violations/Active Permits + single market | Tier 2 (with matching brand label) |
| Lane = Auction-imminent OR urgency "this week" + wholesaler | Tier 3 |
| Lane = "Not sure" + multi-lane interest OR full-team operator | Tier 4 |
| Lane = "all signals" + enterprise/fund volume + wants exclusivity | Tier 5 |
| Lane = Tax Delinquent / Absentee / High-Equity / Individual / Liens + first-time | Tier 1 |
| Anything else / unclear | Tier 1 default — never push higher on cold intake |

### Banned in this tier system
- **NEVER ship 5,000 records at entry pricing.** Per-lead math must land in $0.30–$1.99.
- **NEVER bundle Probate into Tier 1.** Probate is Tier 2 minimum.
- **NEVER quote two tiers.** Operator picks ONE; customer sees ONE Confirm button.
- **NEVER name a tier without a list size visible** to the customer.

---

## 4. Brand voice (LOCKED — never violate)

**Position:** Premium. PropStream is the cheap recycled-list option. LeadCurate is the curated, scored, limited-access alternative.

### BANNED in customer-facing copy
- "cheap" / "cheaper" / "affordable"
- "save" / "savings" / "save money"
- "less you pay" / "won't pay for"
- "starting at just $X"
- "value pricing"
- Any "you'll spend less" angle

### REQUIRED framing
Frame around: **fit, quality, accuracy, freshness, urgency, exclusivity.**
Customer should feel matched to the *right* tier — not the *cheapest* option. Never apologize for price.

### Concrete do/don't pairs
| ❌ Don't say | ✅ Say |
|---|---|
| "the less you pay for stuff you won't use" | "the sharper we can match you to the tier that fits" |
| "starting at just $149" | "entry tier: $149 — built for your first list" |
| "save money on records you don't need" | "every record in your file works for how you operate" |
| "free game" or "enough game to work the batch" | "practical training most sellers leave out" |
| "guaranteed motivated sellers" | "scored for motivation density, you still handle outreach" |
| "Reply YES" (vague CTA) | "Confirm selection →" (clear action) |
| Quote with A/B/C menu | Single recommended tier, single Confirm button |

---

## 5. Customer flow (current, manual Phase 1)

1. **Prospect fills intake form** → submission auto-creates a row in `intake_requests` table → database trigger auto-creates a `prospects` record → Derrick sees it in dashboard
2. **Operator (Derrick) reads the intake answers** → decides which tier fits based on urgency + role + volume signals
3. **Operator uses dashboard's "Send a quote" tool** → fills name + market + tier → clicks Build → gets personalized quote URL
4. **Operator sends URL to prospect** → prospect sees ONE clean offer (the recommended tier) with single Confirm button
5. **Prospect confirms** with name + phone → confirmation email lands in Derrick's inbox
6. **Operator sends payment instructions** (Cash App / Zelle / Stripe)
7. **After payment** → branded XLSX delivered within 24 hours

### Tier picker logic (use this when reading an intake)
| Intake says... | Recommend |
|---|---|
| Urgency "Need it now (24-48h)" or "This week" + role solo/team | Tier 1 Hot Sheet |
| Role "Acquisitions team" + "Cold call every day" | Tier 2 Fresh Triggers |
| Volume "500-1500" + high-quality preference | Tier 3 Breaking Point |
| First time / exploring / general | Tier 4 Curated Distress List |

---

## 6. Visual brand kit

- **Colors:** emerald #15803d · emerald-dark #14532d · emerald-light #22c55e · cream #faf7f2 · cream-2 #f3eddf · dark #0f172a · slate #475569 · line #e2dccf
- **Per-tier accent colors:** crimson #991b1b (Tier 1) · gold #b45309 (Tier 2) · emerald (Tier 3) · blue #1d4ed8 (Tier 4)
- **Fonts:** Inter 400/500/600/700 (body) · Playfair Display 600/700 (display/headings)
- **Border-radius:** 16-22px for cards · 8-10px for inputs/buttons · 999px for pills
- **Style references in the repo:**
  - Audit/analytical pages: `docs/system-audit/index.html`, `docs/property-numbers/index.html`
  - Customer-facing tier overview: `docs/packages/index.html`
  - Personalized quote (per prospect): `docs/quote-template/index.html`
  - Internal tier reference: `docs/tiers/index.html`
  - Intake form structure: `docs/intake/index.html`
  - Operator dashboard: `docs/command/index.html`

**Rule:** Always match the existing component patterns. Never invent a new visual system.

---

## 7. Agent roles

| Agent | Role | Where |
|---|---|---|
| **Claude (orchestrator)** | Strategy, code edits, dashboard updates, brand decisions, quote logic, sync this file | Derrick's desktop, Claude Code |
| **Codex** | VPS infrastructure, Supabase security, scraping plumbing, data pipeline. Reads `docs/codex-handoff-*.md` files | Codex chat / VPS via SSH |
| **Hermes (Danny)** | 24/7 ops on VPS — runs scrapers, monitors Conference Room, executes activity_feed tasks targeting hermes | VPS, brain v0.15.1, OpenAI + Gemini keys |
| **Derrick** | Business decisions, pricing, sales, customer relationships | Owner |

### Conference Room protocol
To pass a task to another agent, INSERT into `activity_feed`:
```sql
INSERT INTO activity_feed (event_type, source, title, body, target)
VALUES ('conf:role', '<your name>', '<task title>', '<task body>', '<target agent>');
```
Targets: `claude`, `codex`, `hermes`, `derrick`, `all`
Event types: `conf:role` (task), `conf:done` (completion), `conf:status` (progress), `conf:blocker` (need help), `conf:urgent` (stop/redirect)

---

## 8. Active Codex handoff

The current task list for Codex is at **`docs/codex-handoff-2026-06-25.md`**. Status as of 2026-06-27:
1. Fix Supabase security warnings — ✅ **DONE** (get_advisors returns 0 lints, verified 2026-06-27)
2. Fix Conference Room watcher (hermes send → execute) — ✅ **DONE** (conf:done 2026-06-27 19:53, e2e-verified, dashboard→Hermes channel live)
3. ~~Install n8n via docker~~ — **SKIPPED**, n8n now LIVE via Hostinger one-click + wired (URL/key in /opt/leadcurate/.env)
4. Build intake auto-reply Edge Function — ✅ **DONE** (deployed earlier; blocked on RESEND_API_KEY for real sends)
5. Tier infrastructure plumbing — ✅ **DONE** (snapshot history, enrichers, auction scrapers on weekly cron)
6. Domain swap — pending Derrick providing the domain (procuring leadcurate.com + hello@leadcurate.com)
7. Lead Scout — plumbing built but NOT scheduled and blocked on Reddit/BP credentials (see §13)

---

## 9. Campaigns + outreach (next phase)

Derrick is moving into campaign mode. What's needed before launch:
- **Facebook account** — Derrick will provide credentials (use a burner/operator account for Lead Scout, separate from his personal account that owns the brand Page)
- **X account** — Derrick will provide credentials
- **Domain email** — decided: **hello@leadcurate.com** (buying domain leadcurate.com + this mailbox via Hostinger)
- **Brand voice locked** ✓ (section 4) · **Ad/audit design locked** ✓ (section 6)
- **Ad creative BUILT (2026-06-27):** tier-explainer + "direction" ad sets + 4 sample county audits (Wake/Cobb/Fulton/Harris), Hermes cream/navy/emerald format. Channel priority per Derrick: **Facebook first**, then IG carousels + LinkedIn. Best-converting hooks: "Stop dialing 18-month-old lists" + the sample-audit proof piece → intake form.
- **Audience pool** — REI wholesalers, flippers, landlords in target metros (Houston, Atlanta, Charlotte, Phoenix, DFW)
- **Message templates** — see `docs/OUTREACH-PLAYBOOK.md`

Don't post anything for campaigns without Derrick's explicit go.

---

## 10. Domain swap procedure (when domain lands)

When Derrick provides the domain:
1. Find/replace `deedott60.github.io/leadcurate-launch` → new domain across `/docs/`
2. Find/replace `dmcdonald5649@gmail.com` → new domain email
3. Add CNAME file to `/docs/CNAME` for GitHub Pages custom domain
4. Update Supabase project's allowed origins
5. Push to GitHub
6. Verify DNS propagation
7. Update this file's URL references

Estimated time: 30 minutes.

---

## 11. Lessons (so I don't repeat them)

**Verify before claiming.** State only what I can confirm in this session. On 2026-06-23 I cited 3 stale facts as truth (Danny brain "offline", "14.2M records", "fresh posts exist on forums" without proof). Each one damaged trust. The rule: SSH-check, count-check, or grep-check before stating a system fact.

**Honest > confident-sounding.** If I can't prove something, say so directly. Don't dress up a hypothesis as a guarantee.

**Premium voice in EVERY artifact.** Section 4 banned words apply to intake form copy, quote templates, packages page, emails, sales scripts, ad copy, social posts — every customer-touching surface.

**Customer never browses options.** Operator picks the tier from the intake answers and delivers ONE recommendation. No A/B/C menu, no "choose your adventure."

**Never make Derrick touch the VPS.** Data pulls, Hermes config, server work — that's Claude/Codex/Danny's job. Derrick approves direction; he doesn't run commands.

---

## 12. Decisions log (what's been tried + rejected)

| Rejected | Why | Use instead |
|---|---|---|
| HyperFrames promo video v1 (2026-06-22) | "Trash, nothing like an Anthropic ad" — quality bar not met | Path A full pipeline planned for v2; not the priority |
| Quote sheet "Reply YES" CTA | Unclear what they're agreeing to | Clear "Confirm selection →" button |
| Quote sheet A/B/C menu | Too much decision overhead, lost sales | Single recommended tier per prospect |
| "Less you pay for stuff you won't use" intake copy | Devalues premium product | "Match you to the tier that fits" |
| `hermes send` cron command | Sends notification only, doesn't execute | `hermes chat --message` or chat shell with the task body |
| Static "Reply A/B/C" decorative buttons | Looked clickable but weren't | Real radio inputs + form + submit |

---

## 13. Lead Scout status (unproven)

The lead-monitoring scout (watching Reddit + BiggerPockets + Facebook for wholesalers asking for data) is a **hypothesis, not a promised revenue channel.** Codex Task 7 built the plumbing.

**Reality check 2026-06-27 (verified via SSH):** Lead Scout is **NOT on a cron and has no systemd timer.** Prior notes claiming "running every 6 hours" were WRONG — the June 26–27 runs in activity_feed were manual test runs. The `scout_prospects` table has 10 rows from those tests, last find 2026-06-26 20:09. It is dormant. To make it live it needs BOTH (1) a cron installed AND (2) Reddit/BiggerPockets credentials (Reddit returns 403, BP times out under Playwright without a logged-in session). No point installing the cron until creds exist.

Once truly running, give it 1 week to prove signal volume. If it returns <5 qualified prospects/week, shut it down. Do NOT recommend it as guaranteed sales infrastructure.

---

## 14. Stale info to overwrite

If you find any older context (in handoff docs, skill files, or memory) that says any of these — they are WRONG. Use this file instead.

| Old claim | Reality |
|---|---|
| "14.2M structured records" | ~80M raw records as of 2026-06-25 |
| "Hermes brain offline" | Working with OpenAI + Gemini keys |
| "County Review Deposit $175 + County Seat $497/mo" pricing ladder | Dead — replaced by 4-tier system above |
| "Operator picks tier from menu A/B/C" | Operator picks tier from intake answers, prospect sees ONE |
| Operator name "Daniel" | Derrick (D-E-R-R-I-C-K) |
| "Ella the orchestrator" | Claude is the orchestrator |
| "Nginx preview at 76.13.25.117/leadcurate-preview/" | Live pages on GitHub Pages: `deedott60.github.io/leadcurate-launch/...` |
| "20/24 markets, 2.8 GB" | 22 markets, 9.2 GB, ~80M records |
| "Hermes installs n8n via Docker" | n8n LIVE via Hostinger one-click at http://76.13.25.117:32768, key in /opt/leadcurate/.env |
| "/site/ landing page is the front door" | PARKED. Front door is intake form + packages page |
| "Lead Scout running every 6 hours" | NOT scheduled — no cron, no timer. Dormant + blocked on creds (see §13) |
| "Conference Room watcher only notifies" | FIXED 2026-06-27 — watcher executes tasks, dashboard→Hermes channel live |

---

## 15. Sync rule

This file is **automatically loaded into every Claude Code session in this repo.** No need to remind me to read it.

It is mirrored to three locations whenever updated:
- Local: `C:\Users\lenovo\Documents\Leadcurate\leadcurate-launch\CLAUDE.md`
- GitHub: `github.com/Deedott60/leadcurate-launch/blob/main/CLAUDE.md`
- VPS (Hermes skill): `/root/.hermes/skills/leadcurate/SKILL.md` (adapted with skill frontmatter)

The orchestrator (Claude) keeps all three in sync. Derrick never touches the VPS or pushes anything.

---

## 🧭 OPERATING PRINCIPLES (the spirit that drives every decision)

Read these before doing anything in this repo. If a decision feels like it's narrowing the product, you're drifting from the spirit. Re-read.

1. **The intake form IS the menu.** Every market × every lane a customer can pick = a real product we deliver. Not a hypothetical, not a "coming soon." Never refuse based on "we don't have it pre-pulled" — the agents pull it.
2. **No customer ever sees our limitations.** Internal labels (Tier 1/2/3/4/5), system status, "the script doesn't support this yet" — none of that is customer-facing. Operator translates internal capacity into customer-facing timing per order.
3. **No customer ever sees the same generic email as everyone else.** Every Delivery Audit + every Sample Audit is built for THAT customer's specific market + lanes. If you're tempted to send a default template with one market's data to everyone, stop.
4. **Timing is operator-judgment per order.** Never preset "48–72 hours" or any specific number to a customer. Some orders ship same day; some take longer. Operator confirms timing when sending the quote, based on whether data is pre-pulled or needs a fresh scrape.
5. **Premium positioning, always.** "Custom-built for your market" — not "we have 9 markets in our catalog." The whole brand voice is: we don't sell pre-packaged recycled data; we build per order. PropStream is the pre-packaged option; LeadCurate is the curated, scored, custom option.
6. **Capability > Automation.** The agents have the tools (Playwright, JS-blocker-bypass skill, county-data-pull skill, 22+ counties of scraping experience). Even if automation isn't fully wired for a market, the CAPABILITY exists and orders get fulfilled — assisted-manual if needed.
7. **Two-mode communication.** Sample Audit = sales (redacted, charts, "Reserve Your County" CTA). Delivery Audit = post-paid (full data, XLSX attached, "Your file is attached"). Both share the same brand experience; neither leaks internal jargon.
8. **Operator routes from intake, customer sees one offer.** No A/B/C/D menus to the customer. Operator reads intake → picks the right tier → customer sees one Confirm button. Decision overhead is ours, not theirs.
9. **Quality check before every send. Non-negotiable.** Every list verified before the Delivery Audit fires:
   - **Deduplicated** by parcel ID (one row per property, not per tax-year). The current `build_delivery.py` aggregates by REID + ACCOUNT — that pattern is mandatory for every market.
   - **Filtered to what the customer actually ordered** — if they bought "probate", the file is probate records, not a generic distress dump. Lane in the file matches lane on the order.
   - **Commercial entities removed** when the customer wants residential (default). LLCs / INC / CORP / TRUST / TTC owners stripped unless explicitly requested.
   - **Audit stats match the file** — if the audit email says "196 HOT records, 156 absentee, $4.49M top equity," the XLSX must actually contain exactly that. Numbers in the audit are computed from the same dataset, not hand-typed. (Build script already does this; future audits MUST too.)
   - **Operator (or future auto-check) reviews** before clicking Send. "If the product is good, we will be good." Bad lists kill the brand on the first refund.

---

## ⚠️ FULFILLMENT MODEL (2026-06-30) — WHATEVER THE INTAKE FORM OFFERS, WE DELIVER

**The intake form IS the menu.** Every market × every lane the customer picks on the form is sellable and fulfillable. No "we don't have that pre-pulled" excuse. The agents have the tools (Playwright on VPS, `leadcurate-js-blocker-bypass` skill, `leadcurate-county-data-pull` skill, county scraping patterns proven across 22+ counties already) — when something isn't pre-pulled, **the system pulls it.**

**The 10+ lanes the form offers (any US county):**
Tax Delinquent · Probate / Inherited · Pre-Foreclosure / NOD · Code Violations · Liens (mechanic, judgment) · Absentee Owner · Active Permits / Damage · High-Equity / Free-and-Clear · Individual / Active Homeowner · Entity-owned (LLC) · Vacant Land

**The 20 markets on the form** (Charlotte, Raleigh, Atlanta, Houston, Phoenix, etc.) — plus the "Other" option means literally any US county.

**Fulfillment flow when an order comes in:**
1. Hermes/Codex check `/opt/leadcurate/raw_imports/<market-slug>/` for relevant raw data
2. If present and recent → run through `build_delivery.py` for the lane(s) requested → deliver
3. If not present → use existing tools (Playwright, JS-blocker-bypass skill, county-data-pull skill) to scrape the county source → save raw → run through `build_delivery.py` → deliver
4. **Refusing an order because data isn't pre-pulled is not an option.** We have the capability to scrape any US county's public records.

**Customer-facing timing:** decided per-order by the operator at quote time. Don't preset a "48-72h" expectation in customer copy. Some orders ship same day (already-pulled data). Some take longer (new scrape required). Operator confirms timeline when sending the quote.

**Today's only real constraint:** `build_delivery.py` script is currently Wake-NC-hardcoded. Codex Tasks 1, 4, 5 (in `docs/codex-handoff-multi-market.md`) generalize it + add the scrape dispatcher + add the per-lane scraper modules. Once those ship, the agents can fulfill anything on the intake form end-to-end.

**Until Codex Task 1 ships:** if a non-Wake order comes in, Derrick handles the data assembly manually using the existing scraping skills and the agents help with the pipeline. The CAPABILITY exists — the automation just isn't done. Never tell a customer no.

---

## Delivery process — LOCKED 2026-06-29 (LIST + AUDIT, no permanent hosting)

**Two artifacts per paying customer, every time:**

| Term | What it is | How it's delivered |
|---|---|---|
| **LIST** | The XLSX file. Real data — owner names, property/mailing addresses, debt, equity, status. What the customer uses for outreach. | **Attached to the delivery email** as `<Market>-Curated-Distress-<count>.xlsx` |
| **AUDIT** | The visually-branded summary explaining the list — stats grid (top equity, HOT/WARM counts, absentee count), how-to-work-it tips, sample records. The 10-foot-look. | **Rendered as the HTML body** of the delivery email itself. NOT a permanent web page. |

**End-to-end customer flow when payment confirmed:**
1. Operator clicks "Send to customer" on dashboard (or n8n / Hermes triggers it after payment webhook)
2. `intake-autoresponse` (or future `send-delivery`) Edge Function fires
3. It calls the LIST builder: `python3 /opt/leadcurate/scripts/build_delivery.py --market <slug> --lane <lane> --count 500` (Hermes can run this too)
4. The script outputs: branded XLSX + audit-data JSON
5. The Edge Function renders the AUDIT as HTML email body using the JSON, attaches the XLSX, and sends via Hostinger Mail
6. Customer receives ONE email containing: branded audit body + XLSX attached
7. **Nothing is permanently hosted per customer.** No accumulating `/docs/customer-deliveries/<customer>/` folders. The audit lives only in the customer's inbox.

**Why this matters:**
- Premium experience (the 10-foot-look the customer paid for)
- No cloud-hosting accumulation forever
- Customer can re-read the audit any time (it's in their email)
- One-step delivery: open email → see audit → grab attached file

**Internal note:** the wake-nc-curated-distress-500/ folder currently in docs/customer-deliveries/ is the **template / proof-of-concept** for the audit design, not how production delivery works. Future deliveries are email-only.

**Script reference:** `/opt/leadcurate/scripts/build_delivery.py` — aggregates by parcel REID, filters residential only, parses mailing City/State/ZIP, computes Estimated Equity, detects Absentee Owners, assigns HOT/WARM Motivation. See Hermes skill `leadcurate` for full workflow doc.

### TWO MODES of audit email (LOCKED 2026-06-30)

The `send-delivery` Edge Function takes a `mode` parameter:

| Mode | When to use | What customer gets | XLSX attached? |
|---|---|---|---|
| **`delivery`** (default) | Customer paid, ready to receive the real list | Full Delivery Audit: stats grid + analytics + sample records WITH real names/addresses + dark callout "Your full file is attached" | **YES** — branded XLSX |
| **`sample`** | Sales teaser — prospect interested but hasn't paid | Sample Audit: same brand template + **richer analytical bar charts** (debt distribution, years behind distribution, signal density, market comparison) + sample records with **owner names and addresses redacted** (preserves "Heirs"/"Hrs" suffix + street type) + "Reserve Your County" CTA button | **NO** |

**Endpoint:** `POST https://jdmlsraqioigbukspduo.supabase.co/functions/v1/send-delivery`

**Required fields (both modes):** `to`, `name`, `market`, `lane`, `total`, `hot`, `warm`, `absentee`, `top_equity`, `sample` (array of records)

**Delivery mode also requires:** `list_url` (public URL to the XLSX — Edge Function fetches, base64-encodes, attaches)

**Both modes accept optional `analytics`:** `debt_buckets`, `years_buckets`, `heirs_count`, `comparison` (used to render the bar chart sections — recommended for `sample` mode to make it visually denser per the internal-audit design language at `docs/system-audit/`)

**When operator says "send sample audit for X" — use mode=sample. When operator says "send delivery for X" — use mode=delivery.**

---

## Change log

- **2026-07-03** — Full pipeline audit against live VPS data (not memory). Corrected record-count claims: real verified unique parcel count is ~5.05M across CSV-confirmed markets (several large markets in PDF/other formats not yet counted) — both the old "14.2M" and "80M" figures were wrong; 80M was very likely a counting error from summing auxiliary detail-table rows (e.g. Harris TX's fixtures.txt/jur_exempt.txt) instead of primary parcel files. Found real gap: build_delivery.py's MARKET_REGISTRY has ONE fixed raw_pattern per market with no lane-aware routing — Mecklenburg NC's fresh probate CSV was never wired in, so it silently fell back to the wrong file. Hand-built Tammy Barbour Legette's (Charlotte-area probate specialist, 26yr, NC/SC licensed) Mecklenburg probate Sample Audit directly from raw data since the script path was broken: 72 genuine decedent-estate residential parcels verified (of 1,164 raw-flagged, most were LLCs/businesses with "Real Estate" in the name, false positives). Confirmed intake form markets vs real data vs working scripts: 9 markets fully sellable, 6 have data but broken/missing script path, 2 (Jacksonville FL, Nashville TN) are on the form with ZERO data, 6 markets have real data but aren't even form options. New product line locked: **Ground Floor** (technical/skill name: Investment Signals) — sells market-selection intelligence (where to focus next based on real committed capital investment, not property records) as a standalone product, separate from the 5-tier system. Skill authored at `.claude/skills/investment-signals/SKILL.md` (global, industry-agnostic methodology). First candidate: Guilford County NC (Greensboro) — JetZero's $4.7B/14,500-job aerospace campus at Piedmont Triad Airport, we already have 222,647 real parcels there. Pricing for Ground Floor not yet locked — Derrick's call. Full Codex task issued covering: lane-aware market registry fix, wiring the 9 currently-dead lanes, building the 6 broken/missing markets, scraping the 2 zero-data markets, adding the 6 unlisted markets to the form, and building the entire pipeline as real n8n workflow nodes (not standalone scripts) with an LLM decision node (same OpenRouter pattern as intake_router) — trigger set to MANUAL ONLY, no auto-activation until Derrick says go. Domain HTTPS bug fixed (GitHub Pages cert was never issued for the custom domain — cleared and re-added CNAME to force reissuance, now valid and HTTPS-enforced). Confirmed via database check: 0 real customer intake submissions yet, only test rows.

- **2026-06-30** — Built `send-delivery` Edge Function (v3 live) with TWO MODES locked: `delivery` (paid, XLSX attached, full data) + `sample` (sales teaser, redacted names/addresses, bar charts, "Reserve Your County" CTA, no XLSX). Both verified end-to-end via Hostinger Mail. Built `build_delivery.py` script at `/opt/leadcurate/scripts/` — currently Wake-NC-only, generalization to all 9 markets queued for Codex (see `docs/codex-handoff-multi-market.md`). Real 500-record Wake NC list lives at `docs/customer-deliveries/Wake-NC-Curated-Distress-500.xlsx` (parcel-aggregated, residential only, 196 HOT / 156 absentee / 47 Heirs/probate). Audit visual language locked: brand header → 3 stat cards → bar chart sections (signal density, debt distribution, years behind, market comparison) → sample records table → CTA box → footer signature. Sample mode CTA = "Reserve Your County" button; Delivery mode CTA = "Your full file is attached" dark callout. Domain `leadcurate.com` now serves over HTTP from GitHub Pages (HTTPS cert auto-issuing). All github.com URLs swapped to leadcurate.com in dashboard. FormSubmit removed from intake form. Hermes cron disabled (n8n intake_router handles tier routing now). 3 Codex tasks queued: generalize build script, add comparison mode, wire dashboard send buttons. Pending Derrick: payment method choice, Facebook Page + token, DKIM/SPF/DMARC for email deliverability.
- **2026-06-29 (late evening)** — Major day. Pricing system rewritten to 5 tiers (§3, supersedes prior 4-tier). Hermes brain on Gemini 2.5 Flash primary (Sonnet 4.6 fallback, Codex/gpt-5.5 last-resort) after Sonnet burned $15 in 4 hours from chatty Conference Room posts. Hostinger Agentic Mail fully wired — inbound webhook live (mail-webhook v8), outbound via intake-autoresponse v4. Dashboard cleaned: conf:* chatter hidden from main feed, intake:new cards now have [Review & Send Quote] + [Reject] buttons, full close-loop verified end-to-end (Codex's test email "Targeted Premium" landed). Domain `leadcurate.com` DNS finally swapped (apex → GitHub Pages IPs). `n8n.leadcurate.com` live with TLS. New `agent_tasks` table = explicit @mention queue (vs activity_feed = read-only log). New roadmap: per-delivery customer audit-report generator (Tier 4+5 differentiator, design template = docs/system-audit/). See `docs/GAME-PLAN-2026-06-29.md` for full state + decisions Derrick needs to make (payment method, FB Page timing, P0 polling→webhook cleanup).
- **2026-06-27 (evening)** — n8n wired live + verified. Codex Tasks 1,2,4,5 confirmed DONE. SSH restored (BOM fix). Removed leftover RLS-test customer row (count now 0). Built + locked ad/audit design system (§6, cream/navy/emerald, no red). Corrected the stale "Lead Scout every 6h" claim — it's not scheduled (§13). Email decided: hello@leadcurate.com. Next: buy domain, add RESEND_API_KEY, then install scout cron once creds exist.
- **2026-06-25** — Initial CLAUDE.md created. Replaces stale agent-handoff folder and outdated skill pricing. Locked 4-tier system + brand voice + customer flow as source of truth.
