# Session Handoff — 2026-06-30 (Launch-Ready)

> **Next session: read this entire doc FIRST, then `CLAUDE.md`.** Pick up exactly where this left off. The product is built. Going public is gated on Derrick's payment choice + FB Page creation.

---

## 0. The spirit of this work (read this first or you'll drift)

This was a hard session. Derrick called out multiple mistakes I made. Capturing the lessons so next session doesn't repeat them:

**Things that wasted Derrick's money/time today — DO NOT repeat:**
1. **I framed the product as a "fixed catalog of 9 pre-pulled markets" repeatedly.** It's NOT. The product is custom-built for any US market × any of 10+ lanes the customer picks on the intake form. The agents have the tools (Playwright, JS-blocker-bypass skill, county-data-pull skill) to fulfill anything. **NEVER tell a customer "we don't have that market."** The capability exists.
2. **I burned ~$15 of OpenRouter credit on Sonnet 4.6 + chatty Conference Room posts.** Then panicked and over-corrected by disabling polling that was actually fine on cheaper models. Don't post `conf:role` tasks unless absolutely necessary. Polling is FREE; LLM calls cost money — and chatty posts wake the LLM.
3. **I claimed emails were delivered when I only had API 200 responses.** Hostinger Mail returning `204 No Content` means accepted, not delivered. **Always check Gmail spam folder + ask user to confirm visually before claiming delivery.** New domains (leadcurate.com) lack email reputation; expect spam routing until DKIM/SPF/DMARC is set up.
4. **I over-explained and offered options when Derrick wanted decisions.** When Derrick asks "what should I do?" — give ONE clear answer, not a menu. He's the operator; he hires me to recommend, not delegate.
5. **I preset customer-facing timelines ("48-72 hours") instead of leaving it to operator judgment per order.** Internal capacity is NOT customer-facing copy. Operator decides timing when sending the quote.
6. **I confused "preview" vs "audit" terminology and made him correct me multiple times.** LOCKED VOCAB: **LIST = the XLSX file** (real data, attached to email). **AUDIT = the branded HTML email body** (visual summary). Two modes: **Delivery Audit** (paid, full data, XLSX attached) + **Sample Audit** (teaser, redacted, bar charts, "Reserve Your County" CTA, no XLSX).
7. **I gave him github raw URLs as "backup" download links.** github.com in any URL = bad for brand. ONLY use leadcurate.com URLs to customers.
8. **I added wordy markdown to copy-paste prompts that broke on paste.** Plain text in a single code block is the rule for Codex prompts.

**Things Derrick valued (do MORE of):**
- Verification with actual data (SSH check, grep, curl, cost-delta from OpenRouter) before stating facts
- Owning mistakes immediately when called out — never defending stale claims
- One clear recommendation rather than 4 options
- Honest "I don't know" instead of confident-sounding guess
- Using existing tools (Playwright, JS-blocker skill) rather than refusing capability

**Tonal note:** Derrick uses voice-to-text. His messages will have typos and homophones ("kodak" = Codex, "Darth" = Danny, "leagues" = skills, "Codecs" = VS Code, "soft fund" = StepFun). Interpret intent, don't get hung up on the exact words.

---

## 1. Current state of the world (LOCKED in CLAUDE.md, verified 2026-06-30)

### Brain stack
- **Hermes (Danny) primary model:** `stepfun/step-3.7-flash` via OpenRouter ($0.20 in / $1.15 out per M tokens — cheapest competent model)
- **Hermes fallback chain:** ✅ Sonnet 4.6 → GPT-4.1 (added 2026-06-30 evening after Derrick approved). Primary stays on StepFun (cheap); fallbacks fire only when StepFun errors/loops. This protects against the Gemini-infinite-loop pattern that burned credits earlier.
- **Verify-delivery LLM review pass:** Sonnet 4.6 via OpenRouter (set up correctly inside the Edge Function for quality verification of every Delivery Audit)
- **OpenRouter balance:** $8.42 remaining as of 2026-06-30 evening

### Why we ended up on StepFun (DON'T undo this without permission)
Derrick had Codex move Hermes off Gemini 2.5 Flash because Flash was:
- Looping on complex queries
- Claiming it couldn't process images
- Repeating itself
StepFun 3.7 was advertised on LinkedIn as a Nous Research partnership (Nous makes Hermes). Derrick chose it intentionally. **Do not switch back to Flash or Sonnet without explicit user request.**

### Infrastructure that's LIVE end-to-end
- `leadcurate.com` domain serving from GitHub Pages
- `hello@leadcurate.com` mailbox (Hostinger Agentic Mail)
- Inbound email pipeline (mail-webhook → inbound_emails table → dashboard live feed)
- Outbound email pipeline (Hostinger Agentic Mail REST API via `send-delivery` Edge Function)
- Supabase: 5 tables live (intake_requests, prospects, inbound_emails, agent_tasks, private.app_secrets)
- Dashboard `/command/`: intake cards with [Review & Send Quote] + [Reject], Send Quote panel with Send to Customer button, hidden conf:* chatter, pipeline view
- n8n: `intake_router` workflow live at `https://n8n.leadcurate.com` (HTTPS via nginx + Let's Encrypt cert)
- Hermes Telegram gateway: active (chat ID 8606329655) — Derrick can message Danny directly

### Edge Functions deployed (all ACTIVE)
- `mail-webhook` v9 — receives inbound mail from Hostinger
- `intake-autoresponse` v4 — legacy, kept for backward compat
- `send-delivery` v3+ — Codex updated with multi-market support. TWO MODES: `delivery` (paid, XLSX attached, full data) + `sample` (redacted, bar charts, no XLSX). Now calls `verify-delivery` before sending in delivery mode.
- `verify-delivery` v1 — Codex built. Quality gate. Deterministic checks (dedup, lane match, stats match, residential filter) + optional Sonnet 4.6 LLM review pass. **Refuses to allow Delivery Audit send if checks fail.**
- `conference-ping` — telegram alerter helper

### What Codex shipped in his last work block (verified via git log)
Commits in the last 4 hours:
- `Fix intake link copy on mobile`
- `Sync delivery verification edge functions`
- `Add multi-market delivery plumbing`
- `add Task 6: verify-delivery Edge Function (quality gate before send)`
- `principle #9: quality contract before every send (deduped, lane-matched, stats verified)`
- `lock operating principles section at top of CLAUDE.md`
- `fulfillment FINAL: intake form is the menu, no refusing orders`

Files added/modified:
- `scripts/leadcurate/build_delivery.py` — generalized for any market+lane
- `scripts/leadcurate/scrape_dispatcher.py` — on-demand county pull dispatcher
- 7 scraper modules under `scripts/leadcurate/scrapers/`:
  - `tax-delinquent/wake-nc.py`, `cobb-ga.py`, `fulton-ga.py`, `harris-tx.py`, `mecklenburg-nc.py`
  - `probate/mecklenburg-nc.py`
  - `active-permits/harris-tx.py`
- `supabase/functions/send-delivery/index.ts` — multi-market plumbing + verify integration
- `supabase/functions/verify-delivery/index.ts` — NEW quality gate

---

## 2. The 9 Operating Principles (locked at top of CLAUDE.md — re-read every session)

These are non-negotiable. If a decision feels like narrowing the product, re-read these:

1. **Intake form IS the menu.** Every market × every lane is sellable and deliverable. Never refuse.
2. **No customer ever sees our limitations.** Internal labels, tier numbers, "we don't have X" — never customer-facing.
3. **No customer gets a generic email.** Every Audit is built for THAT customer's market + lanes.
4. **Timing is per-order operator judgment.** Never preset "48-72h" or any number in customer copy.
5. **Premium positioning always.** "Custom-built" not "we have 9 markets in catalog." PropStream is the pre-packaged option; LeadCurate is curated/scored/custom.
6. **Capability > automation.** Tools exist (Playwright, JS-blocker skill, county-data-pull skill) even if automation isn't fully wired. Orders get fulfilled — assisted-manual if needed.
7. **Two-mode communication.** Sample Audit (sales) + Delivery Audit (paid). Same brand, different content gate.
8. **Operator routes from intake, customer sees ONE offer.** No A/B/C menus. Decision overhead is ours.
9. **Quality Contract.** Every list verified before send: deduped by parcel, lane-matched to order, residential by default, audit stats match the file, operator reviews. Bad lists kill brands.

---

## 3. The 5-tier pricing system (LOCKED in CLAUDE.md §3)

Customer NEVER sees "Tier 1/2/3/4/5" labels. They see ONE recommended tier with adaptive brand label based on lane.

| # | Brand label | Price | Records | Lane scope |
|---|---|---|---|---|
| 1 | Curated Distress List / Active Homeowner / Absentee / High-Equity / Liens (adapts to lane) | **$149 launch / $249 std** | 500 | One foundational lane |
| 2 | Probate Premium / Pre-Foreclosure Premium / Code Violations / Active Permits / The Breaking Point (adapts) | **$249 launch / $397 std** | 250–500 | One court-scrape specialty lane |
| 3 | Imminent Auction Hot Sheet | **$397 launch / $497 std** | 250 | Auction in 30 days |
| 4 | Market Dominance | **$697 launch / $797 std** | 1,000 | ALL 8 lanes, one market |
| 5 | Exclusive Territory | **$1,497 launch / $1,997 std** | 1,000 | All lanes, capped 1 buyer per market |

For custom volume requests, operator uses dashboard "Build Quote" to override price/count.

---

## 4. Active workflows / what triggers what

| Event | Triggers |
|---|---|
| Customer fills intake form | Supabase intake_requests INSERT → DB trigger creates prospect + posts `intake:new` to activity_feed (dashboard card with Review/Reject buttons) → n8n intake_router polls every minute, calls Hermes for tier recommendation, writes `recommended_tier` back |
| Customer email arrives at hello@leadcurate.com | Hostinger webhook → `mail-webhook` Edge Function → row in `inbound_emails` + `conf:status` on dashboard feed |
| Operator clicks "Send Sample Audit" on dashboard | Dashboard POSTs to `send-delivery` with `mode: "sample"` → Edge Function renders teaser HTML (redacted names, bar charts) → email sent via Hostinger, no XLSX |
| Operator clicks "Send Delivery Audit" on dashboard | Dashboard POSTs to `send-delivery` with `mode: "delivery"` + list_url → `verify-delivery` checks dedup/stats/lane/residential → if OK, render audit HTML + attach XLSX → email sent. If verify FAILS → `conf:blocker` posted, no send. |
| Sunday 2:15am | `run_auction_scrapers.sh` cron pulls Mecklenburg/Fulton/Wake auction calendars (feeds Tier 3 Hot Sheet) |

---

## 5. What's still pending (Derrick's hands only)

| Item | Why it matters | Recommendation |
|---|---|---|
| **Payment method** | Can't take money without one | Cash App tag + Zelle email for first 3 sales (zero setup, instant). Open Mercury Bank business account when time permits, then add Stripe (deposits to Mercury). |
| **Facebook Page + Page Access Token** | Locked #1 marketing channel per CLAUDE.md §9 | Create Page from personal account, IG Business linked via Meta Business Suite, generate Page token at developers.facebook.com with `pages_manage_posts pages_read_engagement pages_messaging` scopes. Send token to Claude. |
| **DKIM / SPF / DMARC** on leadcurate.com DNS | Fixes Gmail spam routing for outbound | 15-min Hostinger DNS API task. Have Claude do it next session. |
| **Hermes fallback chain** is empty | If StepFun fails, nothing catches it | Run `hermes fallback add` and pick `anthropic/claude-sonnet-4.6` as fallback 1. Derrick's call. |

---

## 6. Codex queue (per docs/codex-handoff-multi-market.md, after Tasks 1, 4, 5, 6 all shipped today)

Remaining Codex tasks NOT yet shipped:
- **Task 2** — `mode="comparison"` in send-delivery for multi-market comparison emails (when prospect can't decide which county to reserve)
- **Task 3** — Dashboard "Send Sample Audit" + "Send Delivery Audit" buttons (Codex did some of this but verify full integration works end-to-end with verify-delivery)
- **Per-lane scraper modules beyond the 5 priority combos** — add as customer demand surfaces (code violations, pre-foreclosure NOD, absentee for other markets)

When Codex's rate limit clears, paste this one-line prompt:
```
Check activity_feed for new target=codex rows since last session and read docs/codex-handoff-multi-market.md. Remaining work: Task 2 comparison mode and Task 3 full integration test of dashboard buttons end-to-end with verify-delivery quality gate. Per-lane scrapers beyond the 5 priority combos as customer demand surfaces. Post conf:done when complete.
```

---

## 7. Critical "DO NOT BREAK" rules

1. **Never send `mode=delivery` without `verify-delivery` returning `ok: true` first.** Quality Contract is non-negotiable.
2. **Never default to Wake NC data when a different market was ordered.** Customer who paid for Cobb GA gets Cobb GA, period.
3. **Never preset "48-72h" or any specific timing in customer-facing copy.** Operator decides per order.
4. **Never tell a customer "we don't have that market."** Use the scrape dispatcher.
5. **Never post `conf:role` chatter to Hermes without considering token burn.** Polling is free; LLM calls cost money.
6. **Never claim email delivered when only API responded 200.** Confirm visually (inbox/spam).
7. **Never use github.com URLs in customer-facing content.** leadcurate.com only.
8. **Always run `/save-handoff` before closing the context window.**

---

## 8. Pre-launch checklist (for Derrick to do)

Before going public-facing:
- [ ] Pick payment method (Cash App tag + Zelle email at minimum)
- [ ] Create Facebook Page + Instagram Business + Page Access Token
- [ ] (Optional, recommended) DKIM/SPF/DMARC DNS records via Hostinger
- [ ] Add Sonnet 4.6 to Hermes fallback chain
- [ ] Test one end-to-end order (real intake form fill → operator review on dashboard → click Send Sample Audit → confirm receipt)

---

## 9. The one sentence to bring next Claude back online

When Derrick starts the next session and says **"Read CLAUDE.md and the latest session handoff"** — next Claude reads:
1. `/CLAUDE.md` (auto-loaded, has the 9 Operating Principles + Quality Contract + tier system + fulfillment model)
2. This file (`docs/session-handoffs/2026-06-30-launch-ready.md`)
3. Says: "I'm caught up. Wake NC end-to-end is live, multi-market scrapers built, quality gate wired. Outstanding: payment method + FB Page + Hermes fallback chain. What's first?"

---

## 10. Things Derrick said about going public

"We're about to be public-facing probably by the end of the day."

"If the product is good, we will be good."

Take both as briefs. The product IS good — locked terminology, quality contract, two-mode delivery, multi-market support, branded experience. Don't drift from the operating principles. Don't let me (or yourself) narrow the product.

**End of handoff.**
