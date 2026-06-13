# LeadCurate Business Launch Plan

## Purpose

LeadCurate is a quality-controlled property data business for serious real estate investors, wholesalers, and acquisition teams. The first business objective is not to build a full SaaS dashboard. The first objective is to prove that LeadCurate can produce clean, source-attributed, scored, DNC-aware, limited-seat county lead batches that buyers can understand and work.

The launch target is the first $3,000/month from 5-7 serious customers.

## Core offer

LeadCurate sells better county property data, not guaranteed deals.

The paid product includes:

- county/source review
- cleaned and deduped public-record property data
- lead lane classification
- skip-trace enrichment where available
- DNC/status marking where applicable
- score and score reason
- assignment IDs and limited-seat protection
- CSV/XLSX delivery
- practical operator tools, including call prep, MAO worksheet, lead tracker, follow-up cadence, and compliance reminders

LeadCurate does not sell cold outreach, guaranteed motivated sellers, legal advice, or a promise that a buyer will close deals.

## Launch packages

**County Review Deposit: $175 one-time**

Purpose: validates a target county before selling an active seat.

Includes:

- source availability review
- county volume estimate
- lead lane availability
- recommended seat count
- sample file preview
- credit toward first paid month if activated

**Single Batch: $299 one-time**

Purpose: a low-friction proof product for buyers who want to test data quality before a subscription.

Includes:

- one county snapshot where available
- source dates and signal notes
- DNC-aware/contact fields where available
- no recurring subscription

**County Seat: $497/month**

Purpose: ongoing limited-seat county data for a solo operator.

Includes:

- one approved target county
- monthly fresh record updates
- territory suppression/protection
- cleaned CSV/XLSX delivery
- MAO worksheet and call prep

**Operator Seat: $897/month**

Purpose: higher-volume delivery for active teams.

Includes:

- double volume or two smaller counties where supported
- biweekly target delivery
- priority queue assignment
- operator support

**Exclusive Territory: $1,497+/month**

Purpose: buyer blocks other seats in a defined county, ZIP group, or lead lane.

Includes:

- custom territory audit
- single-buyer access rules
- custom scoring/delivery schedule
- custom suppression rules

## Go-live architecture

Use a simple, durable operating stack:

- Landing page: static site on Vercel
- Intake: landing page form submits to a backend endpoint
- Database: Supabase Postgres
- Storage: Supabase Storage or signed object storage for raw files and exports
- Automation: n8n for workflow control
- Processing: Python scripts for parsing, cleaning, dedupe, scoring, and exports
- Email: Resend, SendGrid, or Mailgun for intake alerts and delivery links
- Payments: Stripe Checkout for deposits, single batches, and subscriptions

Formspree/Web3Forms is optional. The stronger business path is to submit the form into LeadCurate's own endpoint, save the request in Supabase, and send an email notification.

## Supabase build order

1. Create the Supabase project.
2. Apply the starter schema from `supabase/schema.sql`.
3. Add the missing workflow tables from `docs/leadcurate-v1-n8n-spec.md`:
   - `workflow_runs`
   - `workflow_events`
   - `raw_files`
   - `lead_exclusions`
   - `lead_quality_checks`
   - `intake_requests`
4. Enable Row Level Security on exposed public tables.
5. Keep service-role keys server-side only.
6. Add a server/API endpoint for the landing page form.
7. Save every intake request to `intake_requests`.
8. Send an email notification for each intake request.
9. Add audit logs for status changes, county review decisions, deliveries, and replacement requests.

Minimum `intake_requests` fields:

- `id`
- `email`
- `target_county`
- `target_state`
- `buyer_profile`
- `preferred_access_option`
- `consent_accepted`
- `source_page`
- `status`
- `notes`
- `created_at`
- `updated_at`

## n8n operating role

n8n should control the workflow, not replace the data engine.

n8n should handle:

- scheduled county source checks
- manual county review triggers
- webhook intake notifications
- running Python scripts
- status alerts
- review handoffs
- delivery emails or signed-link notifications
- failure alerts

Python/Postgres should handle:

- parsing source files
- cleaning names, addresses, parcel IDs, and source dates
- dedupe
- suppression checks
- scoring
- export generation
- assignment/protection rules

The implementation-ready workflow is captured in:

- `docs/leadcurate-v1-n8n-spec.md`
- `docs/leadcurate-n8n-first-county.md`

## First pilot county process

Start with one county and one lead lane. Do not scrape the whole country.

1. Pick a county with accessible public records and enough investor activity.
2. Identify lawful sources:
   - tax delinquent records
   - probate/estate notices where public
   - foreclosure notices where public
   - code violation/vacancy sources where public
   - assessor/parcel records
3. Record source URL, access method, refresh cadence, and terms/access notes.
4. Pull a small lawful sample.
5. Preserve raw files and source dates.
6. Normalize the records.
7. Deduplicate.
8. Classify lane and score quality.
9. Enrich only approved records.
10. Scrub/mark DNC status where applicable.
11. QA the batch manually.
12. Export 10-50 sample rows.
13. Use the sample to validate columns, scoring, and buyer interest.

## County scraping/source policy

Use public-record sources lawfully and conservatively.

Allowed approach:

- use official county/public-record portals where access is permitted
- download public CSV/PDF/report files when offered
- use browser automation only for normal navigation of public pages
- preserve source URLs, source dates, and access notes
- respect terms of service, rate limits, robots guidance, and login restrictions
- stop when a site blocks automation, presents anti-bot challenges, or requires access that has not been granted

Avoid:

- bypassing paywalls, CAPTCHAs, access controls, or anti-bot systems
- pretending DNC-marked numbers are safe to call
- using scraped data without source attribution
- reselling restricted data
- sending unreviewed contact data as a sample

## Skip tracing and DNC workflow

LeadCurate can do skip tracing and DNC-aware delivery, but it needs provider decisions before production.

Recommended flow:

1. Do not skip trace raw records.
2. Clean, dedupe, classify, and score first.
3. Only skip trace records that pass quality and suppression checks.
4. Save provider name, request timestamp, response timestamp, confidence, and matched fields.
5. Run DNC/contact suppression after enrichment.
6. Keep the lead even if a phone is DNC-marked, but mark or remove contact fields according to policy.
7. Export DNC/contact status as a field, not as legal advice.

Provider categories to evaluate:

- property/contact enrichment provider such as BatchData-like APIs
- phone/email validation provider
- DNC/contact suppression provider
- internal suppression list in Supabase

Default policy:

- dedupe: fail closed
- suppression/DNC provider down: fail closed for contact export
- skip trace provider down: fail open without contacts
- delivery export: fail closed if quality gates are incomplete

## Sample batch policy

Sample batches are for sales proof, not mass outreach.

Safe sample batch format:

- 10-25 rows for cold sales conversations
- 25-50 rows for a serious paid deposit review
- include property address, county, lead lane, source type, source date, score, and score reason
- include contact data only if enriched and scrubbed
- mark DNC/contact status clearly
- include a disclaimer that customer is responsible for outreach compliance
- optionally blur owner/contact fields in unpaid previews

Do not imply the sample is "safe to call." Use wording such as:

> Sample records are public-record-derived and DNC-aware where applicable. Buyer is responsible for verifying records, outreach compliance, licensing obligations, and transaction decisions.

## First 30-day execution plan

### Week 1: Foundation

- Finalize landing page and legal pages.
- Choose Supabase project.
- Apply core schema.
- Add `intake_requests` and workflow audit tables.
- Connect landing form to server endpoint.
- Add email alerts for new intake.
- Add Stripe Checkout links for deposit and single batch.

### Week 2: Pilot county setup

- Choose one pilot county.
- Create a `territories` row.
- Create `county_sources` rows.
- Pull 1-3 small public source files manually.
- Preserve raw files.
- Build the first parser/normalizer script.
- Create a sample batch export template.

### Week 3: Data quality and compliance

- Add dedupe logic.
- Add suppression/internal do-not-resell logic.
- Pick skip trace provider.
- Pick DNC/contact suppression approach.
- Add score reasons and exclusion reasons.
- Generate first QA sample batch.

### Week 4: Sales validation

- Create 2-3 sample batches by lead lane/county.
- Reach out to local investors, wholesalers, and acquisition teams.
- Sell county review deposits first.
- Use buyer feedback to adjust columns, score reasons, and delivery format.
- Convert first deposit into County Seat or Single Batch.

## Operating checklist before taking real money

- Legal pages reviewed and placeholders replaced.
- Stripe business account ready.
- Intake form writes to Supabase and emails you.
- County review workflow documented.
- At least one pilot county source reviewed.
- Sample batch includes source dates and score reasons.
- DNC/contact language says "where applicable."
- Replacement policy is written.
- Assignment/protection rule is in database.
- Raw source files are preserved.
- Export file has a disclaimer.

## Immediate next tasks

1. Configure the landing page form endpoint.
2. Create Supabase `intake_requests` and workflow tables.
3. Add email notification provider.
4. Choose the first pilot county.
5. Choose one lead lane for the first sample batch.
6. Identify lawful county sources for that lane.
7. Build the first manual-assisted sample batch.
8. Decide skip-trace and DNC providers before exporting contact fields.

## Important compliance note

This plan is an operating plan, not legal advice. LeadCurate should have its legal templates reviewed before publishing and should confirm data broker, TCPA, DNC, fair housing, state privacy, and public-record resale obligations before selling enriched contact data at scale.
