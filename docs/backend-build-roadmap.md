# LeadCurate backend build roadmap

LeadCurate should be built as a quality-controlled data operation first, not a full SaaS dashboard on day one.

## Backend goal

Deliver lead batches that are clean, source-attributed, scored, DNC-aware, and protected from duplicate resale during the customer access period.

The backend has to prove three things:

1. We know where each record came from.
2. We know why each record made the batch.
3. We can prevent the same assigned record from being sold again inside the protected window.

## Phase 1 — Foundation

Build the core operating system before heavy automation.

- Supabase/Postgres database
- County/source inventory tables
- Customer and territory tables
- Lead batch tables
- Assignment/protection tables
- Delivery tracking
- Replacement request tracking
- Audit logs

Existing starter files:

- `supabase/schema.sql`
- `docs/data-platform.md`

## Phase 2 — County source reviews

Before selling a county seat, create a source review for that county.

Track:

- county/state
- available public-record sources
- source type
- access method
- update frequency
- usable monthly volume estimate
- lead categories available
- source notes and restrictions
- recommended seat count

Outcome:

- sell as 1-seat, 2-seat, 3-seat, exclusive-only, bundle-only, or do-not-sell

## Phase 3 — First manual-assisted batch

Use one target county and build the first controlled batch by hand plus scripts.

Steps:

1. Pull lawful sample records.
2. Preserve the raw file.
3. Parse records into the database.
4. Clean owner/property fields.
5. Remove duplicates.
6. Group records by opportunity type.
7. Add source dates and decision context.
8. Mark DNC/contact status where applicable.
9. Review the batch manually.
10. Export CSV/XLSX.

Do not overbuild dashboards before this works.

## Phase 4 — Automation with n8n

Use n8n as the workflow controller, not the whole data engine.

n8n should handle:

- scheduled source checks
- webhook triggers
- running Python scripts
- status alerts
- manual review handoffs
- email/delivery steps
- failed-source notifications

Python should handle:

- parsing
- cleaning
- matching
- deduplication
- scoring
- export generation

## Phase 5 — Quality system

Add rules that protect the product quality.

Quality checks:

- wrong county
- duplicate in same batch
- missing required field
- stale source date
- contact data below stated standard
- already assigned to another buyer
- restricted/suppressed record
- unclear owner/property match

Each excluded record should have an exclusion reason.

## Phase 6 — Customer delivery

Deliver simple, useful files first.

Initial export columns should include:

- assignment ID
- owner name
- property address
- mailing address
- county/state
- lead category
- source type
- source date
- score
- score reason / decision context
- phone/email if available
- DNC/contact status
- notes

## Tools needed before backend build

Needed soon:

- Supabase account/project or self-hosted Postgres decision
- n8n install decision: same VPS first is fine
- Stripe account for deposits/subscriptions
- email provider: Resend, SendGrid, or Mailgun
- first target county/state to test
- approved source list for that county
- skip-trace/enrichment provider decision
- DNC/contact-compliance workflow decision

Not needed yet:

- full SaaS dashboard
- complex customer portal
- dialer/SMS system
- mobile app
- broad nationwide automation

## Recommended next build order

1. Finalize landing page and form destination.
2. Set up Supabase/Postgres.
3. Apply starter schema.
4. Set up n8n on the VPS.
5. Connect form submissions to database/email.
6. Pick one pilot county.
7. Build the first county source review.
8. Generate the first sample batch.
9. Use the sample batch to refine scoring, columns, and replacement rules.
