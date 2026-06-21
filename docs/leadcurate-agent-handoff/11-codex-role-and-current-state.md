# 11 — Codex: Role + Current State (Handoff)

**For:** Codex agent (when API access is restored)
**From:** Claude (current orchestrator)
**Date:** 2026-06-21

---

## Codex's recommended role on LeadCurate

The user (Daniel) and I have agreed on a clean division of labor between agents. **Codex owns IT, security, and code-quality work.** This plays to your strengths and frees up Claude for business/orchestration work.

### Codex owns

- **Security audits** — regular RLS lint checks via Supabase advisors, GitHub secret-leak scans, dependency audits, OWASP top-10 checks on the dashboard + intake form
- **Debugging** — when the dashboard breaks, when a Supabase query returns unexpected nulls, when GitHub Pages build fails, when a Python processor on the VPS errors
- **Refactoring** — as the codebase grows past a few hundred lines per file, you split, modularize, and tighten
- **Test coverage** — add Playwright tests for the intake form + dashboard flows; add Python tests for the county processors
- **CI / GitHub Actions** — set up build/test/deploy checks on PRs
- **Documentation maintenance** — keep `/docs/` in sync with reality, kill stale claims
- **Monitoring** — set up Supabase Edge Function or simple cron that pings dashboards + form, alerts on regressions
- **Performance** — Lighthouse audits on landing/intake/dashboard, image optimization, JS bundle pruning

### Claude owns

- Business strategy + sales flow design
- Customer outreach templates + copywriting
- County data pulls, processing, and snapshot generation
- Market analysis + competitive positioning
- Pricing / packaging decisions (gathers data, user decides)
- Cross-agent orchestration (planning who does what)
- Branding + visual design choices

### Hermes (Danny) owns (when API is restored)

- Recurring data pulls on cron (daily Wake NC, weekly Tarrant TX, monthly ArcGIS hubs)
- Routine processing of fresh data → updated snapshots
- Customer delivery automation (when payment received → trigger delivery)
- Webhook receivers (Twilio, n8n, Stripe events → Supabase)
- Cheap-model routine work (DeepSeek V3 recommended)

### Daniel owns

- All sales calls, customer relationships
- Final pricing decisions
- Payment method choice
- Outreach (FB groups, IG, BiggerPockets) — manual for Phase 1
- Approvals on anything affecting cost or contracts

---

## Current state of the project (snapshot, 2026-06-21)

### What's live on GitHub Pages

| URL | What it is |
|---|---|
| https://deedott60.github.io/leadcurate-launch/intake/ | Lead intake form, writes to Supabase + emails Daniel |
| https://deedott60.github.io/leadcurate-launch/command/ | Operator OS dashboard (HQ / Inbox / Pipeline / Messages / Workflow / Templates) |
| https://deedott60.github.io/leadcurate-launch/sample-deliveries/ | Preview pages for Houston, Cobb GA, Birmingham AL, Charlotte, Louisville |
| https://deedott60.github.io/leadcurate-launch/site/ | Landing page (PARKED — Phase 3, not yet promoted) |

### Supabase project (`jdmlsraqioigbukspduo`)

- **16 tables**, all with RLS enabled and tiered policies applied
- **`leads`** (34 cols) — legacy intake target, kept for backwards compat
- **`intake_requests`** (14 cols inc. new `role`) — primary intake target as of 2026-06-21
- **`prospects`** (11 cols) — operator dashboard outreach queue
- **`messages`** (12 cols) — manual log for Phase 1, will receive webhooks in Phase 2
- **`activity_feed`** (8 cols) — system events
- **`customers`** (10 cols), **`territories`** (16 cols), **`deliveries`** (9 cols), etc. — Phase 3 schema, ready when needed

### VPS (`leadcurate-vps`, 76.13.25.117)

- 4.7 GB raw county data pulled across 21 markets in `/opt/leadcurate/raw_imports/`
- Processed snapshots in `/opt/leadcurate/snapshots/` for Houston, Cobb, Birmingham
- Playwright 1.60.0 + Chromium installed for JS-blocked sources
- Hermes (Danny) running but **no working API** until Codex bill paid or new provider added
- Codex setup intact in `/root/.codex/` and `/home/codex/`

### Open Phase 1 blockers (Daniel decisions, not technical)

1. **Single-batch price** (suggested: $149 for 200 records)
2. **Payment method handle** (suggested: Cash App, instant + free)
3. **First outreach prospects** (Daniel hasn't started yet)

---

## Codex priorities when API is restored

In order:

1. **Run a full security audit** — `mcp__supabase__get_advisors` on the project, fix any high-priority warnings without breaking the dashboard's anon access
2. **Write Playwright tests** for the intake form (markets → list types → urgency → contact → submit → verify Supabase row + email)
3. **Add GitHub Action CI** — on every PR: lint HTML, validate Supabase migrations don't break schema, run intake form Playwright test
4. **Review the dashboard code** (`/docs/command/index.html`, ~1100 lines) — recommend a split into modules so future edits don't break things
5. **Set up Supabase Edge Function** for any webhook integrations Daniel decides to add (Stripe payment confirmations, Twilio inbound SMS)
6. **Audit the VPS** — security scan, ensure Hermes/Codex/SSH key rotation is clean

---

## Things Codex should NOT do (per Daniel)

- Do NOT touch landing page (`/site/`) without Daniel's explicit go — it's parked until Phase 3
- Do NOT lock pricing decisions — gather data, present options, Daniel decides
- Do NOT add real customer auth yet — Phase 3 work, premature now
- Do NOT push Twilio / WhatsApp integration — Phase 2 work, Daniel will decide cost/benefit later
- Do NOT change the dashboard from anon-access to auth-required without Daniel's go — he wants simple ops, no login wall

---

## Coordination protocol

- **All three agents work from this same repo.** Commits show authorship in the commit message.
- **Use `docs/THE-PLAN.md`** as the canonical sequence (Phase 1 → 2 → 3). Don't drift.
- **Use `docs/OUTREACH-PLAYBOOK.md`** for current customer-acquisition rhythm.
- **Use `docs/PLUMBING-CHECK.md`** for current stack state.
- **Update memory files** in `~/.claude/projects/.../memory/` when learning something durable.

When in doubt: check `docs/THE-PLAN.md`, then ask Daniel.
