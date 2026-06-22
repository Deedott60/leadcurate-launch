# THE PLAN — read this before doing anything

**Owner:** Derrick (Deedott60)
**Last updated:** 2026-06-21
**Status:** Phase 1 active. Do NOT skip ahead.

---

## The order of operations is fixed. Do not jump ahead.

### Phase 1 — Get paying customers FIRST (no subscriptions, no landing page polish)

1. **Find prospects manually** — Facebook groups, REI groups, BiggerPockets, IG, REIA meetups, anywhere real-estate investors hang out.
2. **Send them the intake link** — `https://deedott60.github.io/leadcurate-launch/intake/`. They fill out: market, list type, urgency, volume, contact.
3. **Reply with a preview list** — small redacted sample showing what we have for their market.
4. **They pay before full delivery** — payment method TBD (Cash App / Venmo / Zelle / Stripe). Lock this in before first sale.
5. **Deliver the full list** — HTML preview + XLSX + CSV, like the existing sample deliveries.
6. **Track every step in the dashboard** at `/command/`.

**Goal:** First 5-10 paying customers. Zero subscriptions yet. Cash flowing, real feedback, real testimonials.

### Phase 2 — Operations hub (build only after Phase 1 is generating real income)

A unified dashboard where Derrick can see:
- Inbound messages (intake form submissions, email replies, SMS, WhatsApp)
- Outbound messages he's sent and to whom
- Pipeline status (prospect → contacted → preview sent → paid → delivered)
- What Hermes / Danny is doing
- What Codex is doing  
- What Claude is doing
- SMS via Twilio (when needed)
- All agents controllable from one place

**Do not build this until Phase 1 has 5+ paying customers.**

### Phase 3 — Landing page + subscriptions (build only after Phase 2 ops are working)

The landing page already exists at `/site/index.html` with pricing tiers ($299 / $497 / $897 / $1,497+) and a separate "Check county availability" form.

**Do NOT promote this URL or send traffic to it until:**
- Phase 1 + Phase 2 are working
- Final pricing is locked (see decisions below)
- Subscription billing is set up
- "Limited seats" tracking is real (not a marketing claim)
- $175 deposit refund process is real
- Record assignment / territory suppression is actually enforced

---

## Decisions that are NOT YET LOCKED (don't proceed without Daniel's call)

- **Single-batch price** for Phase 1 sales (preview-then-pay flow). Other session put $299 on the landing page WITHOUT his sign-off. Derrick has not yet confirmed.
- **Payment method** for first customers (Cash App / Venmo / Zelle / Stripe).
- **DNC / phone strategy** — lists currently have addresses + owner names, NOT phone numbers. To sell "non-DNC lists" we need a path: skip-trace service, address-only delivery, or county-pulled phones.
- **Subscription pricing** — Phase 3 only, do not assume the numbers on the landing page are final.

---

## What IS done (don't re-build)

- ✅ Intake form: `/docs/intake/` → writes to Supabase `leads` table + emails dmcdonald5649@gmail.com via FormSubmit
- ✅ Dashboard: `/docs/command/` → outreach tracker, templates, inbound feed, Supabase + localStorage backup
- ✅ Sample deliveries: Houston (Permit Burnout, 1,500 records), Cobb GA (5,678 records), Birmingham AL (21 premium), Charlotte NC, Louisville KY — all live at `/docs/sample-deliveries/`
- ✅ 21 markets pulled (4.7 GB raw data on VPS)
- ✅ Playwright on VPS for any JS-blocked sources
- ✅ JS blocker skill saved
- ✅ Hermes (Danny) installed and running on VPS but **NO WORKING API** until Codex bill paid or new provider added
- ✅ Codex setup intact on VPS

## What is NOT done yet (Phase 1 blockers)

- ❌ Payment method NOT set up (can't take money yet)
- ❌ Single-batch pricing NOT locked
- ❌ Phone numbers NOT pulled for any market (sells as address-only for now)
- ❌ No customers contacted yet
- ❌ Dashboard's "delivered" / "paid" status flow not finalized

---

## Anti-drift rules

When the user says "stay focused," anyone working on this should:

1. Re-read this file BEFORE proposing any new feature.
2. Do not build Phase 2 or Phase 3 things while Phase 1 has open blockers.
3. The landing page at `/site/` is PARKED, not live. Do not send customers there until Phase 3.
4. The dashboard at `/command/` is the operational tool. Improvements to it are in scope for Phase 1.
5. Pricing changes require Derrick's explicit "go" — no Claude session decides pricing alone.
6. If a future session is unclear, ASK Derrick, don't guess.

If you (any AI session) deviate from this plan without explicit user direction, you have wasted his Claude usage limits and money. That is the failure mode. Don't do it.
