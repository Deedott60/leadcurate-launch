# Codex Handoff — LeadCurate VPS Tasks

**Date:** 2026-06-25
**Status:** Codex active again (payment current)
**Operator:** Derrick McDonald (dmcdonald5649@gmail.com)
**Repo:** Deedott60/leadcurate-launch
**VPS:** leadcurate-vps (76.13.25.117) — SSH alias configured
**Supabase project ref:** jdmlsraqioigbukspduo

## Required reading BEFORE you start

1. **`/CLAUDE.md`** — LeadCurate state, 4-tier system, brand voice, customer flow, agent roles
2. **`docs/AGENT-OPERATING-RULES.md`** — universal agent behaviors (verification discipline, communication, conference room protocol, no test data in prod tables, failure-mode awareness)

If conflict between this handoff and CLAUDE.md, CLAUDE.md wins.
If conflict between memory/older docs and direct verification, direct verification wins.

Execute these tasks in order. Each one is self-contained. Mark conf:done in activity_feed as you finish each one.

---

## Task 1 — Fix Supabase security warnings (22 outstanding)

### 1a. Fix two functions with mutable search_path
```sql
-- Run via Supabase MCP execute_sql
ALTER FUNCTION public.notify_conference_ping() SET search_path = public, pg_temp;
ALTER FUNCTION public.auto_pipeline_from_intake() SET search_path = public, pg_temp;
```

### 1b. Convert SECURITY DEFINER functions to SECURITY INVOKER (both reachable by anon/auth role)
```sql
ALTER FUNCTION public.notify_conference_ping() SECURITY INVOKER;
ALTER FUNCTION public.auto_pipeline_from_intake() SECURITY INVOKER;
REVOKE EXECUTE ON FUNCTION public.notify_conference_ping() FROM anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.auto_pipeline_from_intake() FROM anon, authenticated;
-- Trigger-only functions don't need direct execute permission
```

### 1c. Replace `USING (true)` blanket RLS policies on 18 tables

The current policies are too permissive (allow anon/authenticated unrestricted access). Replace per-table:

**For tables that only Derrick should access via authenticated dashboard (customers, deliveries, delivery_leads, lead_assignments, raw_imports, replacement_requests, suppression_records, territories, territory_rights, audit_logs, county_sources):**
```sql
DROP POLICY "auth all <table>" ON public.<table>;
CREATE POLICY "auth read <table>" ON public.<table>
  FOR SELECT TO authenticated USING (auth.uid() IS NOT NULL);
CREATE POLICY "auth insert <table>" ON public.<table>
  FOR INSERT TO authenticated WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "auth update <table>" ON public.<table>
  FOR UPDATE TO authenticated USING (auth.uid() IS NOT NULL);
```

**For tables that anon should only INSERT (intake_requests, leads):**
```sql
DROP POLICY "anon insert <table>" ON public.<table>;
DROP POLICY "anon update <table>" ON public.<table>;
CREATE POLICY "anon insert only <table>" ON public.<table>
  FOR INSERT TO anon WITH CHECK (true);
-- No update/select for anon
```

**For activity_feed, messages, prospects (anon needs SELECT for dashboard public view):**
```sql
DROP POLICY "anon all <table>" ON public.<table>;
CREATE POLICY "anon select <table>" ON public.<table>
  FOR SELECT TO anon USING (true);
CREATE POLICY "auth write <table>" ON public.<table>
  FOR INSERT TO authenticated WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "auth update <table>" ON public.<table>
  FOR UPDATE TO authenticated USING (auth.uid() IS NOT NULL);
```

### 1d. Verify
After all the above, run `get_advisors(type=security)` via MCP. Should return zero `rls_policy_always_true` and `function_search_path_mutable` warnings.

---

## Task 2 — Fix Conference Room watcher (Danny wasn't executing tasks)

The cron script at `/root/.hermes/scripts/conference-watcher.sh` uses `hermes send` (notification only). Change to actually execute. Replace the script with:

```bash
#!/bin/bash
SB_URL="https://jdmlsraqioigbukspduo.supabase.co"
SB_KEY="sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4"
LAST_FILE="/tmp/hermes_last_check"
LAST=$(cat "$LAST_FILE" 2>/dev/null || echo "2026-01-01T00:00:00Z")
date -u +%Y-%m-%dT%H:%M:%SZ > "$LAST_FILE"

MSGS=$(curl -sS \
  "${SB_URL}/rest/v1/activity_feed?target=eq.hermes&created_at=gt.${LAST}&order=created_at.asc" \
  -H "apikey: ${SB_KEY}" \
  -H "Authorization: Bearer ${SB_KEY}")

COUNT=$(echo "$MSGS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo 0)

if [ "$COUNT" -gt "0" ]; then
  echo "[$(date)] $COUNT new task(s) for Hermes" >> /tmp/hermes_conference.log

  # Loop each task and ask Hermes to execute it
  echo "$MSGS" | python3 -c "
import sys, json, subprocess
msgs = json.load(sys.stdin)
for m in msgs:
    title = m.get('title', '')
    body = m.get('body', '')
    prompt = f'Conference Room task from {m.get(\"source\")}: {title}\n\n{body}\n\nExecute this task. Post a conf:done to activity_feed when complete.'
    subprocess.run(['/usr/local/lib/hermes-agent/venv/bin/hermes', 'chat', '--message', prompt], timeout=600)
" >> /tmp/hermes_conference.log 2>&1
fi
```

Then re-enable the cron:
```bash
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/.hermes/scripts/conference-watcher.sh") | crontab -
```

Verify with `crontab -l`. Post a test task to activity_feed targeting hermes from the dashboard and confirm Danny actually executes it within 5 minutes.

---

## Task 3 — Build tier infrastructure (Phase 2 plumbing)

### 3a. Prior-pull retention (enables Tier 2 "Fresh Triggers" detection)
Create `/opt/leadcurate/scripts/snapshot_with_history.py` that:
- Before processing a new pull, copies the previous snapshot CSV to `/opt/leadcurate/snapshots/<market>/_prior/<date>.csv`
- Runs the tier_classifier.py with `--prior` pointing at the most recent _prior file
- Keeps only the last 3 prior pulls per market (delete older)

### 3b. Assessor value enrichment (enables Tier 3 "Breaking Point" detection)
For markets where snapshots lack `assessed_value`, build market-specific enrichers in `/opt/leadcurate/scripts/enrich/`:
- `enrich_cobb_ga.py` — match parcel IDs to Cobb Assessor's parcel database
- `enrich_wake_nc.py` — already has assessor data, just needs mapping
- `enrich_fulton_ga.py` — Fulton Assessor's API exists
- Pattern: input snapshot CSV, output enriched CSV with `assessed_value` column added

Volume estimate: ~half a day per market the first time, then reusable.

### 3c. Auction-calendar scraping (enables Tier 1 "Hot Sheet" detection)
Build `/opt/leadcurate/scripts/auction_scrapers/` with one Playwright script per market that publishes auction calendars:
- `mecklenburg_auctions.py` — county foreclosure calendar
- `fulton_auctions.py` — Fulton sheriff sale calendar
- `wake_auctions.py` — Wake tax sale calendar
- Output: CSV with parcel_id + auction_date columns
- Schedule via cron weekly

---

## Task 4 — Auto-reply on intake form submission

Currently: prospect fills intake → goes to inbox + auto-creates prospect record. No auto-reply.

Build a Supabase Edge Function `intake-autoresponse` that:
1. Triggers on insert to `intake_requests`
2. Reads the prospect's email and intake answers
3. Logic to pick recommended tier:
   - urgency = "Need it now (24-48h)" + "This week" → Tier 1 Hot Sheet
   - role = "Acquisitions team" + urgency = "This week" → Tier 2 Fresh Triggers
   - volume = "500-1500" + role solo → Tier 3 Breaking Point
   - everything else → Tier 4 Curated Distress List
4. Sends auto-reply via Resend/SendGrid (or for v1, FormSubmit's `_autoresponse` field on the form itself)
5. Email body: "Thanks for the inquiry. Based on what you shared, we recommend [tier]. Here's a personalized quote link: [URL with buyer + market + tier params]"

Deploy via `deploy_edge_function` MCP tool.

---

## Task 5 — n8n: WAIT, DO NOT INSTALL

**CHANGED 2026-06-25:** Derrick is doing the Hostinger one-click n8n install himself. **DO NOT run docker install for n8n.**

If you already started the docker install:
```bash
docker stop n8n && docker rm n8n
```

When Derrick confirms Hostinger n8n is up, your job becomes:
1. Get the Hostinger n8n URL from Derrick
2. Configure n8n to talk to Supabase (REST API connection)
3. Build the first workflow: intake_requests → auto-reply email
4. Test end-to-end

Until Derrick confirms, **skip this task** and continue Tasks 1-4.

---

## Task 6 — Domain swap (when domain arrives)

When Derrick provides the domain (expected this week):
1. Find/replace all instances of `deedott60.github.io/leadcurate-launch` in `/docs/` with the new domain
2. Find/replace `dmcdonald5649@gmail.com` with the new domain email (e.g. `derrick@leadcurate.com`)
3. Push to GitHub
4. Configure CNAME file in `/docs/` for GitHub Pages custom domain
5. Verify DNS propagation
6. Update Supabase project's allowed origins to the new domain

Estimated time: 30 minutes once domain is in hand.

---

## Task 7 — Lead Scout (NEW — only after Tasks 1-2 done)

Build prospect-monitoring scraper that watches REI forums for wholesalers asking for data:

### 7a. Reddit watcher
- `/opt/leadcurate/scripts/scout/reddit_scout.py`
- Subreddits: /r/wholesaling, /r/realestateinvesting, /r/realestate
- Keywords: "tax delinquent list", "absentee list", "motivated seller", "need a list", "looking for"
- Cross-reference market mentions against our 22 markets
- Output flagged prospects to new Supabase table `scout_prospects`

### 7b. BiggerPockets watcher
- `/opt/leadcurate/scripts/scout/bp_scout.py`
- BP forum recent activity by category
- Same keyword + market matching

### 7c. Facebook groups watcher (last, requires login)
- Needs a dedicated FB account + Playwright with stored session
- Target REI/wholesaling groups by city

### 7d. Dashboard tab
- New page `/command/scout/` showing flagged prospects
- Each entry: post preview, source URL, market match, suggested DM template, status (new/contacted/closed)

---

## Quick-reference: Activity Feed targets

When you finish each task, post to activity_feed:
```sql
INSERT INTO activity_feed (event_type, source, title, body, target)
VALUES ('conf:done', 'codex', 'Task X complete: <title>', '<what you did>', 'claude');
```

When blocked, post:
```sql
INSERT INTO activity_feed (event_type, source, title, body, target)
VALUES ('conf:blocker', 'codex', 'Blocked on task X', '<what you need>', 'derrick');
```

---

## Don't touch (red zone)

- Production tables: `prospects`, `intake_requests`, `messages`, `customers`, `deliveries` — no test data insertions
- The intake form (`docs/intake/index.html`) — confirm with Derrick before changing form structure
- The landing page `/site/` — Derrick's approval required
- Pricing — Derrick's decision, not a code change

---

## Priority order

1. **Task 1 (security)** — do first, blocks everything else
2. **Task 2 (Conference Room fix)** — unlocks Danny actually executing
3. **Task 5 (n8n)** — quick win, enables future automation
4. **Task 4 (auto-reply)** — biggest customer-experience improvement
5. **Task 3 (tier infrastructure)** — enables real-money premium tiers
6. **Task 6 (domain swap)** — when domain ready
7. **Task 7 (Lead Scout)** — only after foundation is solid
