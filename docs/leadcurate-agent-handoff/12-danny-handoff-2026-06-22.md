# 12 — Danny (Hermes) Handoff — 2026-06-22

**To:** Danny (Hermes agent on VPS, currently running on Codex brain)
**From:** Claude (orchestrator)
**Operator:** Derrick (dmcdonald5649@gmail.com)

---

## Your situation

You haven't touched this project in about a week. Derrick has been working with Claude to build the Phase 1 launch stack. A lot has changed. Read this whole doc before touching anything.

## What you have access to

- **VPS** at `76.13.25.117` (leadcurate-vps alias) — you already have SSH access
- **Supabase** project `jdmlsraqioigbukspduo` — 16 tables, all RLS-enabled
- **GitHub repo** `Deedott60/leadcurate-launch` — all code lives here
- **Gemini API key** — stored in `/root/.hermes/.env` as `GEMINI_API_KEY` (use this as your LLM, Codex brain is temporary)

## What's live RIGHT NOW (don't touch these — they're working)

| URL | What it is |
|---|---|
| https://deedott60.github.io/leadcurate-launch/intake/ | Intake form — writes to Supabase `intake_requests` + emails Derrick |
| https://deedott60.github.io/leadcurate-launch/command/ | Operator OS dashboard — full agent comms, pipeline, templates |
| https://deedott60.github.io/leadcurate-launch/sample-deliveries/ | Sample deliveries (Houston, Cobb, Birmingham, Charlotte, Louisville) |
| http://76.13.25.117/leadcurate-preview/ | Landing page on VPS nginx |

## VPS data state

```
/opt/leadcurate/raw_imports/     ← 22 county folders, ~4.7 GB raw data
/opt/leadcurate/snapshots/       ← processed, sellable files
/opt/leadcurate/scripts/         ← all Python processors live here
```

### What's processed and ready to sell

| Market | Snapshot | Rows |
|---|---|---|
| Harris TX (Houston) | `/snapshots/harris-tx/2026-06-21/` | 1,500 top-ranked (Permit Burnout lane) |
| Cobb GA (Atlanta NW) | `/snapshots/cobb-ga/2026-06-21/` | 5,678 delinquent |
| Jefferson AL (Birmingham) | `/snapshots/jefferson-al/2026-06-21/` | 21 high-balance |
| Wake NC (Raleigh) | `/snapshots/wake-nc/2026-06-22/` | 10,472 delinquent |
| Fulton GA (Atlanta) | `/snapshots/fulton-ga/2026-06-22/` | 368,771 parcel owners (top 5,000 saved) |

### What has raw data but NO clean snapshot yet (your job to fix)

1. **DeKalb GA** — `/raw_imports/dekalb-ga/` exists but the CSV pulled was the geometry/boundaries layer, not the owner records. Need a different ArcGIS item. Try:
   - `https://dcgis-dekalbgis.hub.arcgis.com/api/download/v1/items/7aa40e4967744cb0abadd6cb0dc23c97/csv?layers=0`
   - Or search the DCAT catalog at `https://dcgis-dekalbgis.hub.arcgis.com/api/feed/dcat-us/1.1.json` for items with "owner" or "parcel" in the title

2. **Marion IN (Indianapolis)** — `/raw_imports/marion-in/` exists but the CSV pulled was the TIF district file (no owner data). Need the parcel owner file. Try:
   - `https://data.indy.gov/api/download/v1/items/0d28e222479743baa97f8f4456da7bb4/csv?layers=10`
   - The correct item should have columns like `PARCEL_TAG`, `OWNER_NAME`, `STNUMBER`, `STREET_NAME`

3. **Forsyth NC (Winston-Salem)** — 81 MB parcel file was pulled but has no owner name column. The layer we got has `BLOCKCONTROL`, `BLK`, `LOT` etc. — it's a geometry/tax PIN file. Need the layer with `CURRENTOWNERNAME`. Try:
   - Same URL but a different layer or different item from mapforsyth.org
   - Check DCAT: `https://www.mapforsyth.org/api/feed/dcat-us/1.1.json`

4. **Guilford NC (Greensboro)** — was processed in an earlier session but raw CSV wasn't found when we ran the batch today. Verify the file is still at `/raw_imports/guilford-nc/`. If missing, re-pull:
   - `https://open-data-hub-guilfordgis.hub.arcgis.com/api/download/v1/items/cd3e1ae082b0406aa12ca6bbfbe1b741/csv?layers=0`

## Your immediate tasks (priority order)

### 1. Fix missing snapshots (above 4 counties)
Use the skill file for URL patterns: `/root/.claude` doesn't exist on the VPS, but the skill was also committed to GitHub. Pull the repo:
```bash
git clone https://github.com/Deedott60/leadcurate-launch.git /tmp/lc-ref 2>/dev/null || (cd /tmp/lc-ref && git pull)
# Then read: /tmp/lc-ref/docs/leadcurate-agent-handoff/
```

### 2. Set Gemini as your working LLM
Your Hermes gateway is running (PID around 2857596) but has no working API. Update:
```bash
hermes model  # Select Google Gemini Flash or 1.5 Flash
```
Or edit `/root/.hermes/config.yaml`: change `provider` from `openai-codex` to `gemini` and `model` from `gpt-5.5` to `gemini-2.0-flash`.

### 3. Post to the Conference Room
Once you're running, post a status update to Supabase so Derrick can see you're active. Insert a row:
```bash
curl -sS -X POST 'https://jdmlsraqioigbukspduo.supabase.co/rest/v1/activity_feed' \
  -H "apikey: sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4" \
  -H "Authorization: Bearer sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"conf:status","title":"Danny online — reviewing VPS state","body":"Reading handoff doc. Will post updates as work completes.","source":"hermes"}'
```
Derrick can see this in the dashboard at the 🏛️ Conference Room tab.

### 4. Re-pull and process the 4 broken counties
Use the existing processor pattern from `/opt/leadcurate/scripts/`. All processors follow the same template:
1. Download CSV from ArcGIS URL
2. Find owner column, address column, value column
3. Filter + score + write to `/opt/leadcurate/snapshots/{market}/{date}/`
4. Post completion to Supabase activity_feed

### 5. Set up Hermes cron for recurring pulls (after #1-4 done)
```bash
hermes cron create "Wake NC daily delinquent" --schedule "0 6 * * *" \
  --command "curl -sS -L -o /opt/leadcurate/raw_imports/wake-nc/\$(date +%Y-%m-%d)/delinquent.xlsx 'https://services.wake.gov/collection_extracts/Real_Estate_Delq853_\$(date +%m%d%Y).xlsx'"
```

## What NOT to touch

- Do NOT edit `/docs/command/index.html` or `/docs/intake/index.html` — Claude Code owns those
- Do NOT modify Supabase schema (add/drop tables) — go through Claude if needed
- Do NOT modify the `prospects`, `intake_requests`, `messages` tables directly — those have live data
- Do NOT change the GitHub Pages deployment settings

## How to report back to Derrick

Every time you complete a task, insert a row into Supabase activity_feed with `event_type: "conf:done"` and a summary. He'll see it in real time in the dashboard Conference Room.

## Files to read first

1. `docs/THE-PLAN.md` — the locked 3-phase sequence
2. `docs/OUTREACH-PLAYBOOK.md` — Phase 1 is live now, Derrick is doing outreach TODAY
3. `docs/PLUMBING-CHECK.md` — what's wired, what's manual
4. `docs/leadcurate-agent-handoff/11-codex-role-and-current-state.md` — division of labor between all agents
5. `/root/.hermes/SOUL.md` — your reliability contract (read before posting any status claims)

---

**Bottom line:** Derrick is launching today. Phase 1 outreach starts this afternoon. Your job is to clean up the 4 broken county snapshots and get Hermes cron running so the data stays fresh without manual work. Everything else can wait.

Good luck Danny.
