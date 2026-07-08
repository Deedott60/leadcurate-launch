# Codex Handoff — Audit + Close The Customer Loop

> Read `/CLAUDE.md` §3 (5-tier pricing locked 2026-06-29) FIRST. Supersedes prior handoffs. Three sections: state snapshot, critical close-loop task, audit/fix list. Stay strictly in scope.

---

## SECTION 1 — Current state Claude has verified (don't re-verify; trust and act)

- ✅ **Hermes brain:** `google/gemini-2.5-flash` primary, Sonnet 4.6 fallback, Codex/gpt-5.5 last resort. Hermes cron watcher re-enabled (`*/5 * * * *`, free when idle).
- ✅ **Mail-webhook (inbound):** v8 live. Real Hostinger email from `dmcdonald5649@gmail.com` confirmed → row in `inbound_emails`. `HOSTINGER_WEBHOOK_SECRET` stored in `private.app_secrets`.
- ✅ **intake-autoresponse Edge Function:** v4 deployed with 5-tier adaptive labels. Auto-fire trigger DISABLED (`on_intake_autoresponse` is `disabled` on `intake_requests`). Function works when called manually with payload.
- ✅ **DB triggers on `intake_requests`:** `on_intake_auto_pipeline` ENABLED (creates prospect + posts `intake:new` activity_feed row targeted at `derrick`). `on_intake_autoresponse` DISABLED.
- ✅ **Dashboard `/command/`:** main feed hides `conf:*` (agent chatter) and shows `intake:new` cards with [Review & Send Quote] and [Reject] buttons. Review button navigates to Send Quote panel and prefills `qBuyer`, `qMarket`, `qTier`.
- ✅ **n8n `intake_router` workflow (J4UINOlYYNPPlpGi):** ACTIVE, schedule trigger every minute. Hermes picks tier with new 5-tier logic and writes back `recommended_tier`. (Two existing test rows confirmed correct: probate → "Tier 2 - Probate Premium", empty → "Tier 1 - Curated Distress List".)
- ✅ **Domain:** `leadcurate.com` apex now points to GitHub Pages IPs (185.199.108-111.153). `n8n.leadcurate.com` → VPS 76.13.25.117 with TLS. GitHub Pages cname = leadcurate.com, https_enforced waiting on cert (auto-issues 10–30 min after DNS propagates).
- ✅ **Pricing locked at CLAUDE.md §3** (5 tiers, list sizes per SKU, per-lead math $0.30–$1.99). Brand labels adapt by lane.
- ✅ **`agent_tasks` table** exists (private.app_secrets-style explicit task queue). TLS proxy task is `status='done'`. Three pending: telegram_alerter, tier_mapping_update, probate_discovery — **DO NOT execute** in this session unless explicitly instructed.

---

## SECTION 2 — CRITICAL: close the customer loop (do this FIRST)

**Goal:** when Derrick clicks a button on the dashboard, an email with the personalized quote URL actually arrives in the customer's inbox. Right now the dashboard can build the URL but cannot send it.

### 2a. Add hidden fields on Send Quote panel
File: `docs/command/index.html` — Send Quote panel area (around line 815). Add hidden inputs:
- `<input type="hidden" id="qIntakeId">` (intake_requests.id)
- `<input type="hidden" id="qEmail">` (customer email)

### 2b. Update `window.reviewIntake` to populate them
Same file, the existing `window.reviewIntake` function. Add reads for `Email:` from the event body (parser logic already there for Market, Recommended). Set `qIntakeId` from the event's record (the intake_request_id may need to be added to the activity_feed body — see 2e). Set `qEmail` from the parsed email.

### 2c. Add "📧 Send to customer" button
File: `docs/command/index.html` — next to existing "Build quote link →" button. Disabled when `qEmail` is empty. On click:
1. `if (!confirm('Send recommendation email to ' + qEmail + '?')) return;`
2. POST to:
   ```
   POST https://jdmlsraqioigbukspduo.supabase.co/functions/v1/intake-autoresponse
   Content-Type: application/json
   Body: {
     "record": {
       "id": "<qIntakeId>",
       "name": "<qBuyer>",
       "email": "<qEmail>",
       "markets": ["<qMarket>"],
       "list_type": [],
       "notes": "Operator-approved from dashboard"
     },
     "override_tier_key": "<qTier value>"
   }
   ```
3. On 200: show "✅ Sent to <email>" inline, then `await loadFeed()`.
4. On non-200: show the error message in red.

### 2d. Extend `intake-autoresponse` to honor `override_tier_key`
File: `supabase/functions/intake-autoresponse/index.ts`. In the handler, before calling `pickTier()`, check if `payload.override_tier_key` is one of `entry|specialty|hotsheet|bundle|exclusive`. If yes, build the tier object from a static lookup table matching the 5 brands instead of calling `pickTier`. Use the resolved tier for both the email subject/body and the quote URL. Redeploy via `supabase functions deploy intake-autoresponse`.

### 2e. Add intake_request_id to the dashboard event body
File: SQL — modify `public.auto_pipeline_from_intake()` so the `body` field of the `intake:new` activity_feed insert includes a line like `Intake ID: <new.id>`. This lets `window.reviewIntake` extract it via the existing parser.

### Acceptance test (do this end-to-end before declaring done)
1. From a throwaway email, submit `https://deedott60.github.io/leadcurate-launch/intake/` (or `https://leadcurate.com/intake/` if DNS has propagated by then) with a real email you can check.
2. Verify the `intake:new` card appears on `/command/` HQ feed within 5 seconds.
3. Click **Review & Send Quote** — verify name, market, tier prefill and that the email is set in `qEmail`.
4. Click **📧 Send to customer** — confirm the dialog, then check the throwaway inbox. Email should arrive within 30 seconds from `hello@leadcurate.com` with the recommended tier and quote link.
5. Verify a `quote:sent` row appears in `activity_feed` (the Edge Function posts this).

After acceptance passes, post ONE LINE to `activity_feed`: `quote:sent`, target=`derrick`, title="Close-loop verified". Nothing more.

---

## SECTION 3 — Audit and fix list (after Section 2 is verified, time permitting)

Treat these as a checklist. Do them in order. Each one is small.

### 3a. Stale 4-tier references in HTML (search and replace, NO logic changes)
Run from repo root:
```bash
grep -rnE "Tier ?[1-4]" docs/ --include="*.html" --include="*.md" | grep -viE "tier 5|locked 2026|CLAUDE.md|handoff" | head
```
Any remaining "Tier 1/2/3/4" labels in CUSTOMER-FACING HTML (intake, packages, quote-template, command, share-brief, study, sample-deliveries) need to be updated to the 5-tier names. Do NOT touch docs in `docs/leadcurate-agent-handoff/`, `docs/codex-handoff-*.md`, or historical session-handoffs (those are intentional history).

### 3b. Verify all customer-facing URLs use `leadcurate.com`, not `deedott60.github.io`
```bash
grep -rn "deedott60.github.io" docs/ --include="*.html"
```
Should return zero hits. If any remain, replace with `leadcurate.com` (no path change).

### 3c. Verify `dmcdonald5649@gmail.com` is replaced with `hello@leadcurate.com` in customer-facing copy
```bash
grep -rn "dmcdonald5649@gmail.com" docs/ --include="*.html"
```
Should return zero hits. Replace if found. Do NOT touch `CLAUDE.md` historical entries that reference the old address.

### 3d. Verify intake_router workflow uses 5-tier system in its OpenRouter prompt
Open n8n workflow `J4UINOlYYNPPlpGi`. The "Recommend tier" node has a prompt. It must reference the 5 tier brand labels (`entry / specialty / hotsheet / bundle / exclusive`) and the adaptive lane labels (Probate Premium, Active Homeowner List, etc.). If it still references "Tier 1 Imminent Auction" / "Tier 4 Curated Distress List" 4-tier framing, update it. After updating, save and let the next test intake validate.

### 3e. Verify Hermes brain config is sane
```bash
ssh leadcurate-vps "hermes config show | head -8"
```
Expected: `model.default: google/gemini-2.5-flash`, `model.provider: openrouter`, `model.base_url: https://openrouter.ai/api/v1`. Fallback list should include `anthropic/claude-sonnet-4.6` then `openai-codex/gpt-5.5`. If different, fix via `hermes config set` (don't edit yaml by hand).

### 3f. Verify the `on_intake_auto_pipeline` trigger posts the right event_type
Quick check via Supabase SQL:
```sql
select pg_get_functiondef(oid) from pg_proc where proname = 'auto_pipeline_from_intake';
```
Body insert into `activity_feed` should use `event_type = 'intake:new'` and `target = 'derrick'`. If it still says `conf:status` and `target = 'claude'`, replace per Claude's last update.

---

## OUT OF SCOPE — do NOT touch in this session

- ❌ Facebook / Instagram / X / LinkedIn wiring
- ❌ Telegram alerter (queued in agent_tasks; leave it)
- ❌ Probate-portal discovery across 22 counties
- ❌ Payment provider integration (Stripe, Cash App, Zelle)
- ❌ Multi-lane scraper expansion (Track B from prior handoff)
- ❌ New n8n workflows beyond `intake_router`
- ❌ Re-enabling the `on_intake_autoresponse` DB trigger (manual button = the new path)
- ❌ Anything in `/site/` (parked landing page)

When done with Section 2 (acceptance test passing) AND any items from Section 3 you completed, post ONE LINE to `activity_feed`:
- event_type: `conf:done`
- source: `codex`
- target: `derrick`
- title: `Audit + close-loop complete — <count> Section 3 items done`
- body: brief bullet list of what got fixed

That's it. Stop after.
