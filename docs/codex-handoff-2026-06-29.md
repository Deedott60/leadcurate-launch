# Codex Handoff — 2026-06-29

> Read `/CLAUDE.md` first. This handoff supersedes `codex-handoff-2026-06-28.md`.
>
> Strategic shift: Derrick wants **every lane available for every sellable market** + n8n as the visual workflow layer + every agent + automation wired into the dashboard's activity_feed as the central nervous system.

---

## Status snapshot (verified 2026-06-29)

- ✅ Hermes brain: `anthropic/claude-sonnet-4.6` (Sonnet 4.6) via OpenRouter; Gemini 2.5 Flash on 8 auxiliary slots; fallback chain: GPT-4.1 → Codex/gpt-5.5. Verified live.
- ✅ Hostinger Agentic Mail INBOUND fully live: mail-webhook v8 deployed (`verify_jwt=false`), `HOSTINGER_WEBHOOK_SECRET` + `HOSTINGER_MAIL_TOKEN` stored in `private.app_secrets` and VPS env. Test email from `dmcdonald5649@gmail.com` confirmed end-to-end.
- ✅ `mail-webhook` posts `conf:status` to `activity_feed` on every inbound. Dashboard sees it live.
- ⏳ Outbound send wrapper (Task 1c from prior handoff) — verify status / complete if not done.

---

## Track A — n8n plumbing (NEW, was deferred — now active)

n8n is live at `http://76.13.25.117:32768`. API key in `/opt/leadcurate/.env` as `N8N_API_KEY`. **No workflows built yet.**

### A1. Bootstrap & connect
1. Verify n8n reachable. Pin a stable port behind nginx/Caddy with TLS (currently bare http + Docker-assigned port — not safe for live customer data).
2. Install Supabase credential in n8n (project URL + service_role key) — use the Supabase node, not raw REST.
3. Install HTTP Request credential profiles for: Hostinger Agentic Mail API (`api.mail.hostinger.com`, Bearer `HOSTINGER_MAIL_TOKEN`), OpenRouter, Hermes CLI proxy (later).
4. Post `conf:status` to activity_feed on n8n boot.

### A2. First three workflows (build in this order)

**Workflow 1 — `intake_router`**
- Trigger: Supabase row inserted in `intake_requests`
- Steps:
  1. Pull row (market, list type, urgency, volume, contact)
  2. Call Hermes (`hermes -z "..."`) with prompt: "Given this intake, recommend tier (1-4) + draft 2-sentence operator note explaining why"
  3. Insert into `prospects` (already auto-trigger, but enrich with the AI recommendation)
  4. Post `activity_feed` row: `event_type=intake:new`, `target=derrick`, title with recommended tier
- Acceptance: submit a test intake → row appears in `prospects` with `recommended_tier` populated within 60s.

**Workflow 2 — `inbound_email_triage`**
- Trigger: Supabase row inserted in `inbound_emails`
- Steps:
  1. Read raw_payload (use `raw_payload->data->plainBody` if present, else fetch `bodyUrl`)
  2. Call Hermes with: "Classify this email: {prospect_question, payment_confirmation, complaint, spam, other}. Extract: market mentioned, urgency level. Output JSON."
  3. Update `inbound_emails` row with `category`, `extracted_market`, `urgency` columns (add columns if missing)
  4. Post `activity_feed` row with the category. If `prospect_question` or `payment_confirmation`, target=derrick urgent.
- Acceptance: send a test email → row in `inbound_emails` has category within 30s.

**Workflow 3 — `quote_send`**
- Trigger: manual HTTP webhook (called by dashboard's "Send Quote" button)
- Inputs: prospect_id, tier, market, lane(s)
- Steps:
  1. Pull prospect contact + quote template
  2. Personalize template with prospect data
  3. POST to Hostinger Agentic Mail API to send via `hello@leadcurate.com`
  4. Insert into `outbound_emails` (create table if missing — symmetric to `inbound_emails`)
  5. Post `activity_feed`: `quote:sent`
- Acceptance: click dashboard button → email arrives at Derrick's test address within 10s, row in `outbound_emails`, activity feed updates.

### A3. Document each workflow
- Export n8n workflow JSON to `docs/n8n-workflows/` so they're versioned in git.
- Add a `docs/n8n-workflows/README.md` explaining each one's trigger, steps, and how to test.

---

## Track B — Multi-lane scrape expansion (NEW)

**Today:** 9 sellable markets, mostly single-lane (Tax Delinquent). **Goal:** every sellable market offers EVERY available lane on demand.

### B1. Schema first
Create normalized lane storage:
```sql
create table if not exists market_lanes (
  id uuid primary key default gen_random_uuid(),
  market_slug text not null,         -- e.g. 'wake-nc', 'cobb-ga'
  lane text not null check (lane in (
    'tax_delinquent','probate','code_violations','pre_foreclosure',
    'active_permits','owner_records','high_equity','absentee'
  )),
  status text not null default 'planned'
    check (status in ('planned','scraping','ready','failed')),
  record_count int default 0,
  last_pulled_at timestamptz,
  source_url text,
  notes text,
  unique (market_slug, lane)
);
alter table market_lanes enable row level security;
```

### B2. Seed the 9 sellable markets × 8 lanes
Insert 72 rows (9 markets × 8 lanes). For each row, mark `status='ready'` if data already exists, else `status='planned'`. The 8 markets currently selling Tax Delinquent → mark their tax_delinquent row as `ready` with record_count from existing data.

### B3. Per-lane scraper modules
Build one scraper module per lane in `/opt/leadcurate/scrapers/<lane>/<market_slug>.py`. Modules already exist for tax_delinquent + a few others — leverage them. New lanes to add (priority order):
1. **Probate** — county probate court records (Mecklenburg NC first — well-documented portal)
2. **Code violations** — city/county code enforcement portals
3. **Pre-foreclosure / NOD** — county recorder
4. **Owner records / Active homeowners** — county assessor (Fulton already has this — replicate pattern)
5. **High equity** — computed lane (filter from tax_delinquent + assessor data)
6. **Absentee** — computed lane (filter from owner_records where owner address ≠ property address)

Each scraper:
- Reads target URL from `market_lanes.source_url` for this (market, lane)
- Outputs to `/opt/leadcurate/data/raw/<market>/<lane>/<date>.json`
- Updates `market_lanes.status`, `record_count`, `last_pulled_at`
- Posts `activity_feed` row: `lane:pulled` with target=all

**Use the `leadcurate-js-blocker-bypass` skill** for any JS-rendered portals. Playwright is installed on VPS.

### B4. On-demand pull endpoint
Build `/opt/leadcurate/scripts/pull_market.py`:
- Args: `--market wake-nc --lanes probate,tax_delinquent,code_violations` (or `--all-lanes`)
- Behavior: runs each requested scraper module sequentially, captures errors, posts `activity_feed` events
- Wired so Hermes can call it: when a customer requests a market we don't have all lanes for, Danny invokes this script.

### B5. Scheduled refresh
- Weekly cron: `0 3 * * 0` runs full refresh on all (market, lane) pairs where status='ready'. Stale data is worse than no data.

---

## Track C — Dashboard as central nervous system

The dashboard already reads `activity_feed`. What's missing is making sure **every meaningful event** flows through it, and the dashboard surfaces them as actionable cards.

### C1. Standardize the event taxonomy
Add or confirm these event_type values:
- `conf:role`, `conf:status`, `conf:done`, `conf:blocker`, `conf:urgent` (existing)
- `intake:new`, `intake:triaged` (Workflow 1)
- `quote:sent`, `quote:confirmed` (Workflow 3 + intake response)
- `mail:inbound`, `mail:outbound`, `mail:triaged` (Workflow 2)
- `lane:pulled`, `lane:failed`, `lane:available` (Track B)
- `pay:received` (later, when payment provider chosen)
- `fb:comment`, `fb:dm`, `fb:reaction` (Track 3 from prior handoff, when token lands)

Add `event_type` index if missing: `create index if not exists activity_feed_event_type_idx on activity_feed (event_type, created_at desc);`

### C2. Dashboard triggers view
Add a `/command/triggers` route (or panel) that:
- Shows live `activity_feed` rows, grouped by `event_type` family
- Each card has a primary action (e.g. `intake:new` → "Send Quote" button → fires Workflow 3)
- Each agent's last heartbeat (Hermes, Codex, n8n) shown as colored dot — green if active in last 10 min

### C3. Agent heartbeats
Every 5 min from each agent, post a `conf:status` heartbeat to activity_feed. Already partial — n8n needs to start doing it once it's bootstrapped (a cron Schedule trigger node, posts to Supabase).

---

## What to NOT do in this batch

- ❌ Payment integration (Derrick deferred — pick provider later)
- ❌ FB / IG wiring (waits on Derrick creating Page + token — separate handoff)
- ❌ Lead Scout cron (still blocked)
- ❌ Landing page (`/site/`) work
- ❌ Twilio / WhatsApp / phone number
- ❌ Pricing changes — under separate audit (see `docs/pricing-audit-for-manus.md`)

---

## Order of execution

1. **First:** A1 + A2/Workflow 1 (intake_router) — fastest win, demonstrates n8n + dashboard trigger loop end-to-end.
2. **Then:** B1 + B2 (schema + seed) — no scraping yet, just structure.
3. **Then:** A2/Workflow 2 (email triage) — leverages already-live mail-webhook.
4. **Then:** B3 — start with probate for Mecklenburg NC (small, well-documented, validates the pattern).
5. **Parallel as you go:** C1 + C2 + C3.

Post `conf:status` when starting each, `conf:done` when complete. Block via `conf:blocker` to `derrick` if you need a credential or a decision.
