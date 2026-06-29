# Plumbing Check — Phase 1 Outreach Stack

**Last verified:** 2026-06-21
**Status:** Ready for week-1 outreach. SMS automation deferred to Phase 2.

---

## End-to-end flow walkthrough

1. **Daniel finds a prospect** on FB group / BiggerPockets / IG / wherever
2. Opens [the dashboard](https://leadcurate.com/command/) → clicks **🔗 Copy intake link** in topbar
3. Pastes link in DM/SMS with cold-intro template ("SMS — cold intro" or "DM — IG/FB/Twitter")
4. Daniel adds prospect to **Pipeline** tab (name, contact, channel, source)
5. Status: **Queued → Reached out** (auto-flips when he uses the "Copy msg" button on a prospect card)

6. **Prospect clicks the link** → fills [intake form](https://leadcurate.com/intake/)
   - Form asks: markets, list type, urgency, volume, name/phone/email, role, notes
7. Submission writes to **TWO destinations simultaneously**:
   - Supabase `intake_requests` table (primary)
   - dmcdonald5649@gmail.com via FormSubmit (backup email)
8. Dashboard's **Inbox tab** shows the new submission **in real-time** (Supabase realtime subscription → 🔔 toast in dashboard)

9. **Daniel sees the inbound** → clicks **→ Pipeline** to import into outreach queue
10. Replies using **★ Preview + quote** template — fills in [market], [N], [PRICE]
    - Sends sample-deliveries URL as the preview
    - Status: **Preview sent**
11. Prospect agrees → Daniel sends payment instructions (**$ Cash App** / **$ Zelle** / **$ Stripe** template)
    - Status: **Quote out**
12. Money received → Daniel sends **★ Payment received** template, processes the list
    - Status: **Paid**
13. Daniel emails the file using **★ Delivery email** template
    - Status: **Delivered**
14. 3 days later → **⤴ Day-after check-in** + **⤴ Referral ask** templates

---

## Component status

| Component | Status | Notes |
|---|---|---|
| Intake form HTML | ✅ Live | `/docs/intake/` |
| Intake form → Supabase `intake_requests` | ✅ Live | Confirmed via dashboard sync indicator |
| Intake form → email (FormSubmit) | ✅ Live | First submission requires you to click an email-confirmation link; after that, every submission emails directly |
| Dashboard `/command/` | ✅ Live | 6 pages: HQ, Inbox, Pipeline, Messages, Workflow, Templates |
| Realtime sync (Supabase channel) | ✅ Live | New inbound rings 🔔 in dashboard within ~1 second |
| LocalStorage backup of prospects | ✅ Live | Works even if Supabase down |
| Templates (18 total) | ✅ Live | Pipeline + Replies + Payment + Post-delivery |
| Sample delivery pages | ✅ Live | Houston, Cobb GA, Birmingham AL, Charlotte, Louisville |
| Copy intake link button | ✅ Live | Topbar in dashboard |

## Messaging / SMS plumbing

| Channel | Phase 1 (now) | Phase 2 (later) |
|---|---|---|
| SMS outbound | Send from Daniel's phone manually; log in **Messages** tab | Twilio webhook → Supabase Edge Function → auto-log |
| SMS inbound | Manually log replies in **Messages** tab | Twilio webhook auto-pushes |
| WhatsApp | Manual (Daniel's phone) | Twilio WhatsApp API or WhatsApp Business API |
| Instagram / Facebook DM | Manual | Manual long-term (Meta has no good DM automation API for personal use) |
| Email | Daniel's Gmail | Could add SendGrid / Resend for templated sends later |

**For week 1-2: 100% manual is fine.** Don't pay for Twilio yet. Log every message Daniel sends/receives in the dashboard's Messages tab (just paste the body + tag direction). That itself becomes the data we'll need to decide if Twilio is worth $20/mo.

## What auto-logs vs. what Daniel logs manually

**Auto-logs** (Supabase realtime):
- New intake form submissions → Inbox
- Pipeline status changes → kanban updates
- Prospect adds → Pipeline

**Manual logs:**
- Outbound SMS/DM (Daniel pastes in Messages tab)
- Inbound replies (Daniel pastes in Messages tab)
- Notes on a prospect (Daniel types in the drawer)
- Activity events (Daniel adds via the "+ Event" button on HQ or Workflow page)

For Phase 1, this is acceptable. Manual logging takes 10–15 sec per message. It creates the audit trail he needs without spending $$$ on automation.

## What's deferred to Phase 2

These are NOT set up and shouldn't be set up yet:
- Twilio account + phone number
- WhatsApp Business API
- Stripe payments integration (use a Stripe payment link template instead — manual)
- Hermes agent webhooks → dashboard
- Codex agent webhooks → dashboard
- n8n workflow automation

Each of these has a placeholder card on the dashboard's **Workflow** page so they can be wired in when Phase 2 starts.

## Decisions still open (block first quote)

1. **Single-batch price** — placeholder `$[PRICE]` in templates
2. **Payment method handle** — `[YourCashtag]` / `[your-email-or-phone]` / `[STRIPE_LINK]` in templates
3. **Standard list size per tier** — e.g., $149 = 200 records, $249 = 500 records

Once these are locked, fill them into the templates (or tell Claude to bake them in) and the system is fully ready.
