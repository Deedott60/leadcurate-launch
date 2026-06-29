# Codex Handoff — 2026-06-28

> Read `/CLAUDE.md` first. This handoff supersedes `codex-handoff-2026-06-25.md`.
>
> Goal of this batch: **make the dashboard the single control surface for everything — inbound email, outbound email, Facebook engagement, Hermes activity.** Derrick should not have to touch SSH, n8n, or APIs.

---

## Status snapshot (verified 2026-06-28)

- ✅ Hermes brain moved to **OpenRouter + DeepSeek V3** (primary). Codex (gpt-5.5) demoted to fallback only. Gemini removed.
- ✅ `OPENROUTER_API_KEY` stored in `/opt/leadcurate/.env` and `/root/.hermes/.env`.
- ✅ `HOSTINGER_API_KEY` works — confirmed against developers.hostinger.com (billing/domains/VPS endpoints return 200).
- ✅ `leadcurate.com` confirmed in Hostinger portfolio (id 32364955, expires 2027-06-28).
- ❌ Resend is **CANCELLED** — not needed. Use Hostinger Agentic Mail instead (see Task 1).

---

## Task 1 — Wire Hostinger Agentic Mail (replaces all "Resend" tasks)

**Why this matters:** Hostinger shipped Agentic Mail (June 2026). It gives us MCP server + webhooks + REST API + allow/block lists on `hello@leadcurate.com` — exactly the agentic stack we want, no third-party send service needed.

### 1a. (DERRICK ONLY, in hPanel — Codex cannot do this)
1. hPanel → Emails → `leadcurate.com` → Agentic mail → **API** section
2. Click **Create API token**
3. Name: `leadcurate-agent-prod`
4. Scope: **Selected mailboxes** → `hello@leadcurate.com`
5. Permissions: `Manage all SMTP/IMAP actions` + `Manage webhooks` (both)
6. **COPY THE TOKEN IMMEDIATELY** — Hostinger only shows it once. Paste it to Claude in chat (Claude will write it to VPS env, never echo it).
7. While in hPanel, take a screenshot of the **MCP Server** sub-page (URL + connection instructions) — share with Claude.

### 1b. Codex: store the token and wire the webhook receiver
Once Derrick provides the token:
1. Add to VPS env: append `HOSTINGER_MAIL_TOKEN=<value>` to `/opt/leadcurate/.env` (chmod 600).
2. Create Supabase table `inbound_emails`:
   ```sql
   create table if not exists inbound_emails (
     id uuid primary key default gen_random_uuid(),
     received_at timestamptz not null default now(),
     from_addr text not null,
     subject text,
     preview text,
     raw_payload jsonb not null,
     handled boolean default false
   );
   alter table inbound_emails enable row level security;
   ```
3. Deploy a Supabase Edge Function `mail-webhook`:
   - POST endpoint, validates `Authorization: Bearer <HOSTINGER_MAIL_TOKEN>` header
   - Inserts the payload into `inbound_emails`
   - Also inserts into `activity_feed`: `event_type='conf:status'`, `source='hostinger-mail'`, `title='New email from <from>'`, `target='derrick'`
4. Register the Edge Function URL as the webhook destination in hPanel → Agentic mail → Webhooks → event `message.received`.
5. Send a test email to `hello@leadcurate.com` and verify (a) row appears in `inbound_emails`, (b) item appears on dashboard live feed.

### 1c. Codex: wire outbound send via Agentic Mail REST API
- Base URL: `https://api.mail.hostinger.com` (confirm exact paths from hPanel → Agentic mail → API → docs)
- Auth: `Authorization: Bearer <HOSTINGER_MAIL_TOKEN>`
- Build a tiny `/opt/leadcurate/scripts/send_mail.py` wrapper: `send_mail(to, subject, body_html, body_text=None)`
- **First wiring target:** the existing intake autoresponse Edge Function (currently blocked) — swap its send call to use this wrapper.

### 1d. Claude: wire the MCP server into the LeadCurate Claude Code session
Once Derrick shares the MCP URL screenshot from hPanel, Claude will add the Hostinger Mail MCP entry to `.mcp.json` in this repo so future sessions in this dir can read/send mail directly (same pattern as the existing Supabase MCP).

---

## Task 2 — Domain swap (parallel; safe to run after Task 1 webhook is live)

§10 of CLAUDE.md. Two halves:

### 2a. DERRICK (Hostinger hPanel → DNS for leadcurate.com)
Add the four GitHub Pages A-records on the apex + one CNAME for `www`:
- A `@` → `185.199.108.153`
- A `@` → `185.199.109.153`
- A `@` → `185.199.110.153`
- A `@` → `185.199.111.153`
- CNAME `www` → `deedott60.github.io`

Then in GitHub repo → Settings → Pages → set Custom domain = `leadcurate.com`, enable Enforce HTTPS.

### 2b. Codex: code find/replace + CNAME file
- Find/replace `leadcurate.com` → `leadcurate.com` across `/docs/` (32 refs in 13 files — grep first to confirm).
- Find/replace `dmcdonald5649@gmail.com` → `hello@leadcurate.com` in customer-facing copy (NOT in CLAUDE.md historical notes).
- Add `docs/CNAME` containing only the line `leadcurate.com`.
- Update Supabase project allowed origins to include `https://leadcurate.com`.
- Push to main.
- Verify with curl after DNS propagates.

---

## Task 3 — Facebook Page wiring (after Derrick creates Page + token)

Derrick is creating: FB Page for LeadCurate + linked Instagram Business + a Meta developer App that generates a long-lived **Page Access Token**. Token comes to Claude in chat.

### Codex (once token is in env):
1. Add to VPS env: `FB_PAGE_ID=<id>`, `FB_PAGE_TOKEN=<token>`, `IG_BUSINESS_ID=<id>`.
2. Create Supabase table `social_posts`:
   ```sql
   create table if not exists social_posts (
     id uuid primary key default gen_random_uuid(),
     platform text not null check (platform in ('facebook','instagram','linkedin','x')),
     external_id text,
     posted_at timestamptz,
     content text,
     image_url text,
     status text default 'draft',
     reactions_count int default 0,
     comments_count int default 0,
     last_polled_at timestamptz
   );
   ```
3. Build `/opt/leadcurate/scripts/fb_post.py` — posts to Page via Graph API.
4. Build `/opt/leadcurate/scripts/fb_poll.py` — pulls engagement on existing posts every 15 min, updates `social_posts`, posts notable events (new comment, >5 reactions) to `activity_feed`.
5. Add the poll script to root crontab: `*/15 * * * * /opt/leadcurate/scripts/fb_poll.py >> /var/log/fb_poll.log 2>&1`
6. Dashboard `/command/` gets a Social tab showing the `social_posts` table + comment feed.

**Out of scope here:** no automated replying to comments. Derrick approves replies for now — Danny just surfaces them.

---

## Task 4 — Hermes (Danny) brain audit (low-priority cleanup)

Master file says Hermes is v0.15.1; actually v0.17.0 (201 commits behind upstream).
- **Don't auto-upgrade.** Current setup works and we just re-pointed the brain.
- After Tasks 1-3 are stable, schedule a one-off `hermes update` window during a quiet hour, with rollback plan (snapshot `~/.hermes/config.yaml` + `auth.json` first).

---

## Tasks explicitly NOT in this batch (do not start)

- ❌ Resend setup — cancelled, use Hostinger Agentic Mail
- ❌ n8n SMTP/IMAP workflow — superseded by Agentic Mail webhook
- ❌ Twilio / WhatsApp Business / phone number — deferred until first paying customers
- ❌ Lead Scout cron — still blocked on Reddit/BP creds, and Derrick said no Reddit
- ❌ Landing page work (`/site/`) — still parked per THE-PLAN

---

## Conference Room protocol for this batch

Each task: post `conf:status` when starting, `conf:done` when complete. If blocked, `conf:blocker` targeting `derrick`. Claude monitors and updates this file + CLAUDE.md as tasks complete.
