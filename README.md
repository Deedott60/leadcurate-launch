# LeadCurate Launch

LeadCurate is a premium property data company for serious real estate investors.

Positioning: **Give away the basic operating tools. Sell the better data.**

## Current contents

- `site/index.html` - premium landing page prototype using the LeadCurate palette/logo direction.
- `site/terms.html`, `site/privacy.html`, `site/refund-policy.html`, `site/compliance.html` - legal/compliance page templates that still need business details and attorney review.
- `docs/leadcurate-agent-handoff/README.md` - start-here folder for another agent, auditor, or build tool.
- `docs/leadcurate-agent-handoff/08-local-and-github-inventory.md` - canonical local/GitHub inventory to prevent mixed LeadCurate folders.
- `docs/leadcurate-business-launch-plan.md` - business plan, offer ladder, go-live architecture, sample batch policy, and first 30-day plan.
- `docs/sample-batch-automation.md` - no-spend sample batch workflow.
- `scripts/build_sample_batch.py` - starter script for turning a lawful public-record CSV into a LeadCurate sample batch.
- `docs/product-strategy.md` - simplified offer, pricing, territory model, and launch focus.
- `docs/data-platform.md` - first data architecture and pipeline plan.
- `docs/leadcurate-v1-n8n-spec.md` and `docs/leadcurate-n8n-first-county.md` - implementation-ready n8n workflow specs.
- `supabase/schema.sql` - starter Postgres schema for Supabase.

## Launch thesis

LeadCurate turns messy public-record property data into cleaned, source-dated, scored, limited-seat batches. Skip tracing and DNC/contact status are added where available and where the provider/compliance workflow is configured. Counties are sold as limited seats based on actual county volume.

## First milestone

Get to $3,000/month with 5-7 serious customers, not high-volume cheap list sales.

## Next agent start point

For any future agent or audit tool, point it to:

`docs/leadcurate-agent-handoff/README.md`

That folder is the organized business/build handoff. It summarizes the plan, positioning, operator-kit structure, data workflow, automation stack, compliance posture, and next-agent checklist in one place.
