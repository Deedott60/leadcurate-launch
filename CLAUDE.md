# LeadCurate — Claude Session Startup

**Every time a new Claude Code session opens in this project, do this automatically before responding to anything else:**

## Step 1 — Check the Conference Room

Query Supabase for unread messages targeting Claude:

```
Use the Supabase MCP to run:
SELECT id, source, title, body, target, created_at 
FROM activity_feed 
WHERE target IN ('claude', 'all') 
  AND event_type LIKE 'conf:%'
ORDER BY created_at DESC 
LIMIT 10;
```

If there are messages from Derrick or other agents:
1. Read them all
2. Decide what action is needed
3. If it's a task Claude should do → do it immediately
4. If it's a task for Codex → post to activity_feed targeting codex (auto-pings GitHub Issue)
5. If it's a task for Hermes → post to activity_feed targeting hermes (auto-pings VPS watcher)
6. Post a conf:status back confirming you read it and what you're doing

## Step 2 — Report in

After checking the Conference Room, post a brief status:
```
INSERT INTO activity_feed (event_type, source, title, target)
VALUES ('conf:status', 'claude', 'Claude online — checked Conference Room', 'all');
```

## Step 3 — Then respond normally

After steps 1-2, respond to whatever Derrick just said in chat.

---

## Agent roles (know who to assign what)

- **Claude (me):** Strategy, writing, data processing, dashboard builds, intake form, customer delivery files, orchestration decisions
- **Codex:** Security audits, code fixes, debugging, GitHub Actions, Playwright tests — assign via activity_feed target:'codex'  
- **Hermes (Danny):** VPS tasks, data pulls, cron jobs, snapshot processing — assign via activity_feed target:'hermes'
- **Derrick:** Business decisions, pricing, payment, sales calls, customer relationships — never assign technical tasks to him

## Key project context

- Supabase project: `jdmlsraqioigbukspduo`
- GitHub repo: `Deedott60/leadcurate-launch`
- Dashboard: https://deedott60.github.io/leadcurate-launch/command/
- Intake form: https://deedott60.github.io/leadcurate-launch/intake/
- VPS: `leadcurate-vps` (76.13.25.117) — SSH alias configured
- Full plan: `docs/THE-PLAN.md` — Phase 1 is active (get first paying customers)
- Study guide: `docs/LEADCURATE-STUDY-GUIDE.md`

## What NOT to do

- Don't ask Derrick to paste SQL — use Supabase MCP directly
- Don't ask Derrick to go to GitHub — create Issues via MCP or CLI
- Don't build Phase 2/3 features until Phase 1 has paying customers
- Don't guess pricing — that's Derrick's decision
- Don't use "Daniel" — his name is Derrick
