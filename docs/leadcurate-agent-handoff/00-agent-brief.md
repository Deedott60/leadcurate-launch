# 00 - Agent Brief

## Project

LeadCurate is a county-based property data product for real estate investors, wholesalers, and acquisition teams.

The business sells cleaned, source-dated, scored, limited-seat property lead batches. It does not sell guaranteed deals, guaranteed motivated sellers, or cold outreach services.

## Current goal

Get to a working launch path:

1. Landing page live.
2. Intake form connected.
3. Supabase database ready.
4. One pilot county selected.
5. One lawful public-record sample batch produced.
6. Buyer outreach starts using the sample batch.
7. Sell county review deposits before promising full seats.

## Current repository state

Important files:

- Landing page: `site/index.html`
- Legal pages: `site/terms.html`, `site/privacy.html`, `site/refund-policy.html`, `site/compliance.html`
- Business plan: `docs/leadcurate-business-launch-plan.md`
- n8n workflow spec: `docs/leadcurate-v1-n8n-spec.md`
- First county workflow: `docs/leadcurate-n8n-first-county.md`
- Sample batch automation: `docs/sample-batch-automation.md`
- Sample script: `scripts/build_sample_batch.py`
- Starter schema: `supabase/schema.sql`

## Important unresolved setup

- The landing page form still needs a real backend endpoint.
- Supabase project/table setup is not complete in this clone.
- Skip-trace and DNC providers are not selected.
- Legal page placeholders need real business details and attorney review.
- First pilot county and first source are not selected.

## Key instruction for future agents

Do not turn this into a generic SaaS dashboard first. Build the quality-controlled data operation first: source review, raw import preservation, cleaning, dedupe, scoring, suppression, sample export, and audit trail.
