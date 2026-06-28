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

### What's PARKED (do not touch without Derrick's go)
- `/site/` landing page — Phase 3 work
- Pricing changes — Derrick decides
- Production tables — never insert test data

---

## 3. The 4-Tier Product System (LOCKED 2026-06-23)

Customer NEVER sees "Tier 1/2/3/4" labels — that's internal. They see one tier (the one we recommended based on their intake) with the brand tier name.

### Tier 1 — Imminent Auction Hot Sheet
- **Price:** $397 launch (first 5 buyers) → $497 standard
- **Cadence:** One-time per sheet (NOT subscription — auctions are episodic)
- **Trigger:** verified auction date in next 30 days, score forced 95-100
- **Buyer:** fast-moving wholesalers who can contract this week

### Tier 2 — Fresh Triggers Feed
- **Price:** $197/week launch → $297/week standard
- **Cadence:** Weekly subscription — the ONLY recurring tier
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
- **Buyer:** everyone — foundational entry product

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
- **Per-tier accent colors:** crimson #991b1b (Tier 1) · gold #b45309 (Tier 2) · emerald (Tier 3) · blue #1d4ed8 (Tier 4) — **INTERNAL `docs/tiers/` PAGE ONLY. Never use these in ADS.**
- **AD/AUDIT DESIGN LOCKED (2026-06-27):** Ads + sample audits use **cream #faf7f2 + navy #0f172a + emerald #15803d/#22c55e ONLY**. NO red/gold/crimson/blue in ads (Derrick killed red explicitly). Match Hermes' approved format: Playfair wordmark+headlines, Inter body, one dark navy data card per ad, dark navy pill CTA, green-dot eyebrow pill. Sample audits: "SAMPLE" stamp, CSS-blurred real addresses (not fake XXXX boxes), show the 4 LANES (not "Tier 1-4"), equity as High/Med/Low (not 0-100 score), no owner-name/skip-trace columns. Approved closer line: "Stop dialing 18-month-old lists." Full recipe in user memory `feedback_leadcurate_ad_design.md`.
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

## Change log

- **2026-06-27 (evening)** — n8n wired live + verified. Codex Tasks 1,2,4,5 confirmed DONE. SSH restored (BOM fix). Removed leftover RLS-test customer row (count now 0). Built + locked ad/audit design system (§6, cream/navy/emerald, no red). Corrected the stale "Lead Scout every 6h" claim — it's not scheduled (§13). Email decided: hello@leadcurate.com. Next: buy domain, add RESEND_API_KEY, then install scout cron once creds exist.
- **2026-06-25** — Initial CLAUDE.md created. Replaces stale agent-handoff folder and outdated skill pricing. Locked 4-tier system + brand voice + customer flow as source of truth.
