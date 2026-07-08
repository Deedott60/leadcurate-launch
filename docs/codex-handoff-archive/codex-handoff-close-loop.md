# Codex Handoff — Close The Loop

> Read `/CLAUDE.md` §3 first (5-tier pricing). This is the SHORTEST remaining work to make the customer-side flow fully usable. No new infrastructure, no scope creep. Two small things.

---

## Current state (verified by Claude — don't re-verify, just trust and act)

- ✅ Customer fills intake form → DB row → `intake:new` event card lands on dashboard with [Review & Send Quote] + [Reject] buttons
- ✅ Dashboard `/command/` → "Send Quote" panel pre-fills name, market, tier when Review button clicked
- ✅ Existing "Build quote link →" button generates personalized URL like `https://leadcurate.com/quote-template/?buyer=X&market=Y&tier=Z`
- ✅ `intake-autoresponse` Edge Function (v4 deployed) has working send logic via Hostinger Mail — token in `private.app_secrets`, mailbox auto-discovered
- ✅ Auto-fire trigger on intake disabled — sending is gated on a manual click from the dashboard
- ❌ **Gap:** dashboard "Build quote link →" only builds the URL; it does not POST to the Edge Function to actually email the customer. **That's task 1.**

---

## Task 1 — Wire "Send to customer" button on Send Quote panel (PRIORITY)

**File:** `docs/command/index.html` — search for `qBuyer`, `qMarket`, `qTier` block (around line 818) and `buildQuote()` function.

**What to add:**

1. A **second button** next to "Build quote link →" labeled **"📧 Send to customer"**. Disabled until a buyer name + market + tier are filled in AND there is an associated email address. To pull the email: if the panel was opened from a dashboard intake card, store the `intake_request_id` in a hidden field. Otherwise prompt the operator for the email.

2. On click, this handler must:
   - Confirm with the operator (`confirm()` dialog showing "Send recommendation email to <email>?")
   - POST to the Edge Function:
     ```
     POST https://jdmlsraqioigbukspduo.supabase.co/functions/v1/intake-autoresponse
     Content-Type: application/json
     Body: {
       "record": {
         "id": "<intake_request_id>",
         "name": "<qBuyer>",
         "email": "<resolved_email>",
         "markets": ["<qMarket>"],
         "list_type": [],
         "urgency": "operator-override",
         "notes": "Operator-approved send from dashboard"
       },
       "override_tier_key": "<qTier value: entry|specialty|hotsheet|bundle|exclusive>"
     }
     ```
   - On success (200): show "✅ Sent to <email>" inline, post `quote:sent` to `activity_feed` (no need to call again — the Edge Function already posts), refresh feed.
   - On failure: show the error from the Edge Function response in red.

3. **Modify** `supabase/functions/intake-autoresponse/index.ts` to honor the new optional `override_tier_key` field in the payload. If present, skip `pickTier()` and use the provided key + a corresponding adaptive brand label from the 5-tier system in `CLAUDE.md §3`. Redeploy via `supabase functions deploy intake-autoresponse`.

4. **Update the Review button handler** in the dashboard (function `window.reviewIntake` in `docs/command/index.html`) to also stash the intake's email + intake_request_id in hidden fields on the Send Quote panel, so Step 1 can read them.

**Acceptance test:**
- Fill out the intake form at `https://deedott60.github.io/leadcurate-launch/intake/` with a real email (your own throwaway).
- Verify the `intake:new` card appears on `/command/`.
- Click **Review & Send Quote**.
- Verify name, market, tier are pre-filled in the Send Quote panel.
- Click **Send to customer**.
- Verify: (a) confirmation dialog appears, (b) an email arrives at the test address, (c) a `quote:sent` row appears in `activity_feed`.

**Do NOT touch:** pricing, Hermes config, Conference Room cleanup, any other workflow, any other Edge Function, any agent_tasks rows.

---

## Task 2 — Convert intake_router to webhook trigger (OPTIONAL, only if time permits)

The n8n workflow currently polls Supabase every minute. With Gemini Flash this is ~$0.001/day, basically free. But cleaner to make it event-driven.

1. In n8n, open workflow `J4UINOlYYNPPlpGi` (LeadCurate - intake_router). Replace the "Every Minute" schedule trigger with a **Webhook trigger** node at path `/webhook/intake-router`, method POST.
2. In Supabase Dashboard → Database → Webhooks: create a new webhook on table `intake_requests`, events `INSERT`, type HTTP, URL `https://n8n.leadcurate.com/webhook/intake-router`. Add header `Content-Type: application/json`.
3. Inside the workflow, the first node after the webhook should read `$json.record` (the inserted row) instead of querying for pending intakes.
4. Test by submitting a fresh intake; verify the workflow ran exactly once in n8n execution history.

Skip this task if Task 1 took the full session — it's a polish item, not a blocker.

---

## Out of scope (do NOT touch in this session)

- ❌ Pricing or tier structure (locked in `CLAUDE.md §3`)
- ❌ Facebook / Instagram / X wiring
- ❌ Telegram alerter
- ❌ Probate-portal discovery
- ❌ Lead Scout
- ❌ Any agent_tasks row beyond Task 1/2 above
- ❌ Conference Room / activity_feed schema changes
- ❌ Hermes config (brain, fallback, gateway)

When Task 1 is verified passing, post ONE-LINE `quote:sent` (or `conf:done` if you must) to `activity_feed` with target=`derrick` and stop.
