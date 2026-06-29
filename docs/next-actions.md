# Next actions

Last updated: 2026-06-21

## Completed

- [x] Supabase project connected (`jdmlsraqioigbukspduo` · Dashboard/Form LeadCurate · ACTIVE_HEALTHY)
- [x] Supabase schema applied — 15 tables: `intake_requests`, `prospects`, `messages`, `activity_feed`, `leads`, `customers`, `territories`, `county_sources`, `raw_imports`, `territory_rights`, `lead_assignments`, `deliveries`, `delivery_leads`, `replacement_requests`, `suppression_records`, `audit_logs`
- [x] Intake form (`docs/intake/index.html`) wired to `intake_requests` table + FormSubmit email fallback
- [x] Landing page form (`site/index.html`) wired to `intake_requests` via Supabase REST API + FormSubmit fallback
- [x] Command OS dashboard (`docs/command/index.html`) — HQ, Inbox, Pipeline (Kanban), Messages, Workflow, Templates, ⌘K palette, Realtime subscriptions
- [x] Legal page placeholders replaced — LeadCurate LLC, North Carolina, Mecklenburg County
- [x] Data pulled for 20 of 24 target markets (~2.8 GB on VPS at 76.13.25.117)
- [x] Processing pipeline proven for 3 markets: Guilford NC, Jefferson KY, Shelby TN

## Still open — data pipeline (requires VPS access)

- [ ] Build Discovery Snapshots for 17 markets with raw data but no processed product yet (pattern: `/opt/leadcurate/scripts/process_*.py`)
- [ ] Crack 3 blocked markets needing browser automation:
  - Harris TX (Houston) — HCAD JS-rendered bulk zip page
  - Cobb GA — rotating dated PDF filenames on JS-rendered page
  - Jefferson AL (Birmingham) — React SPA at eringcapture.jccal.org
- [ ] Schedule recurring pulls via cron (Wake NC daily, Tarrant TX weekly, ArcGIS hubs monthly)

## Still open — business setup

- [ ] Create Stripe deposit link ($175 county review) and single-batch link ($299)
- [ ] Pick first pilot county and lane to go to market with
- [ ] Build first operator-kit documents from `docs/leadcurate-agent-handoff/03-operator-kit.md`
- [ ] Decide skip-trace and DNC/contact suppression providers before exporting contact fields
- [ ] Update legal pages once formal LLC is registered (currently using "LeadCurate LLC" placeholder)
- [ ] Wire email notification for new `intake_requests` rows (Supabase Edge Function or Resend/SendGrid webhook)

## Key URLs

- Command OS: https://leadcurate.com/command/
- Intake form (send to prospects): https://leadcurate.com/intake/
- Landing page: https://leadcurate.com/
- Supabase dashboard: https://supabase.com/dashboard/project/jdmlsraqioigbukspduo
- VPS: 76.13.25.117 (srv1564456 · Ubuntu 24.04 · Docker 29)

## Agent orientation

- Read `docs/leadcurate-agent-handoff/README.md` first
- Data pipeline state: `docs/leadcurate-agent-handoff/09-data-pipeline-status.md`
- Business plan: `docs/leadcurate-business-launch-plan.md`
- n8n workflow spec: `docs/leadcurate-v1-n8n-spec.md`
