---
name: lead-data-product-planning
description: Plan, critique, and launch premium lead/data products built from public records, enrichment, suppression, and buyer-ready delivery.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [business-planning, lead-generation, data-products, compliance, pricing, go-to-market]
---

# Lead Data Product Planning

Use this skill when helping plan, critique, launch, or operationalize a lead/data product business — especially products built from public records, proprietary cleaning workflows, skip-trace/enrichment services, compliance suppression, territory rights, and buyer-ready exports.

This is a business/operator skill, not a scraping-evasion skill. Help the user build a high-quality, lawful, durable data product. Do not provide anti-bot bypass, CAPTCHA evasion, fingerprint spoofing, IP rotation to avoid blocks, or access-control circumvention.

## Core posture

The strongest positioning is usually not “we sell leads.” It is:

> We turn messy source data into cleaned, scored, source-attributed, compliance-aware, buyer-ready intelligence.

Prefer premium/high-trust positioning over commodity list sales:

- limited access instead of mass resale
- transparent source dates instead of mystery data
- confidence scoring instead of hype
- suppression/audit logs instead of blind exports
- customer execution responsibility instead of guaranteed outcomes

## First-pass critique checklist

When reviewing a plan, score it across:

1. **Market pain** — does the buyer already pay for data/software/services?
2. **Differentiation** — why not use generic list vendors or big platforms?
3. **Data source feasibility** — can sources be accessed lawfully and reliably?
4. **Data quality moat** — cleaning, parsing, dedupe, matching, scoring, auditability.
5. **Compliance posture** — DNC/opt-out/suppression, source rights, disclaimers.
6. **Unit economics** — sourcing + enrichment + QA + delivery costs vs subscription price.
7. **Operational complexity** — source-specific parsers, refresh cadence, manual review needs.
8. **Trust/proof** — sample file, source dates, confidence scores, replacement policy.
9. **Go-to-market** — founder-led sales before broad ads.
10. **Overbuild risk** — avoid building a full SaaS before paid validation.

## Launch shape

For an early-stage lead/data product, recommend a manual-assisted MVP before a full platform:

1. Landing page
2. Availability/fit form
3. Paid reservation or deposit
4. Customer/territory database
5. Manual or semi-automated source audit
6. Sample file / proof artifact
7. CSV/XLSX delivery
8. Simple protected customer resource page
9. Replacement request workflow
10. Documentation and disclaimers

Do not start with a full CRM, dialer, SMS blaster, marketplace, mobile app, or complex dashboard unless there is already strong paid demand.

## Offer/pricing simplification

If the plan has many offers, collapse the public launch into 3–4 clear choices:

- **Reservation / Territory Hold** — low-friction paid validation; credited toward first month.
- **Core Seat** — default monthly subscription for one territory or data lane.
- **Operator Seat** — higher-volume or priority plan for active buyers.
- **Exclusive / Custom Territory** — custom-priced premium tier after audit.

Move add-ons to upsell or post-purchase:

- templates / operator guide
- specialty data lanes
- priority zip clusters
- rollout support
- custom exclusivity

Avoid public cheap per-lead pricing as the primary model; it commoditizes the product. Use per-lead pricing only for add-ons, overflow, one-time samples, or active-subscriber specialty packs.

## Territory and exclusivity logic

If selling geographic or category exclusivity, force explicit definitions:

- territory: state, zone, county, zip cluster, corridor
- data/lead lane: residential, commercial, tax, probate, foreclosure, absentee, land, REO, nurture, etc.
- exclusivity type: territory-exclusive, record-exclusive, preferred access, non-exclusive
- delivery range: expected range, not guaranteed count
- suppression rule: which records are blocked from resale and for how long
- blocked inventory: what future sales this exclusivity prevents

Never sell broad exclusivity cheaply without calculating blocked inventory.

## Quality and fulfillment language

Prefer process-based fulfillment instead of outcome guarantees.

### Strategic education / “free game” positioning

For premium lead/data products, a small amount of buyer education can be strategic rather than wasteful. If the user wants to “give away part of the game” (for example MAO/offer logic, prioritization criteria, why raw records are weak, or how county review works), preserve that intent while keeping it concise and professional.

The purpose is to prove the brand understands the buyer’s actual workflow after delivery, not to turn the landing page into a course. Frame education as trust-building and differentiation from generic list sellers:

- explain why raw/stale lists are weak,
- show that county source availability and seat count are reviewed before selling access,
- help buyers understand why a record is worth reviewing,
- connect source context and score reasons to outreach/offer prioritization,
- avoid promising that the data itself closes deals.

A useful trust line is: “We show the work because serious buyers are tired of mystery lists.”

### Customer-facing copy taste for lead products

For public landing pages, translate data-operation language into buyer value. A nontechnical investor should understand the section immediately without needing to know data pipelines.

Use concrete, professional labels:

- "Find the right records" / "Source" for source review.
- "Refine the records" for cleanup, dedupe, and normalization.
- "Add decision context" for source dates, DNC status, contact details, score reasons, and prioritization hints.
- "Reserve" or "Assignment protection" for holding assigned records back during an access period.
- "Deliver the batch" for the final file handoff.

Avoid both extremes:

- Too technical/internal: routing, suppress, assignment window, lead lanes, contactability, source accessibility, data quality, quality filters.
- Too casual/childish: clean the obvious mess, send the batch, obvious junk, records that obviously do not belong.

When pricing a limited-seat lead product, avoid vague lines like "priced by effort" or "priced by data quality." Prefer plain buyer-facing logic such as "reviewed before we sell seats," "market size," "usable lead volume," "source coverage," "expected monthly range," and "number of available buyer seats."

Prefer process-based fulfillment instead of outcome guarantees.

Say:

- expected monthly delivery range
- source date included
- confidence score included
- DNC-status marked where applicable
- replacement available for records failing stated quality standard
- customer must verify claims before outreach

Do not say:

- guaranteed deals
- guaranteed motivated sellers
- legal to call
- safe to text
- fixed lead count regardless of source activity

Define “qualified lead” as a record that passes the product’s source, dedupe, routing, scoring, suppression, and delivery checks for the purchased lane — not a guaranteed prospect who will answer or close.

## Replacement policy

Keep replacement criteria strict. Replace only for quality/process failures such as:

- duplicate delivered in the same customer batch
- wrong territory or lead lane
- parsing error on a critical field
- record already assigned under an exclusivity window
- missing required field that should have been present
- contact data fails the stated quality standard

Do not replace simply because:

- seller was not motivated
- seller did not answer
- buyer did not close
- property was not a good deal
- customer failed to follow up

## Data architecture starter

Common tables/collections:

- customers
- territories
- source_inventory / county_sources
- raw_imports
- properties
- owners
- lead_records
- enrichment_results
- suppression_records
- lead_assignments
- deliveries
- replacement_requests
- audit_logs

Keep raw/source artifacts and hashes when possible. Preserve original fields before cleaning.

### Quality-first backend posture

When the user says the product must be the best-quality lead source, treat the backend as a quality control system, not just a form/database app. The first backend deliverable should prove source attribution, decision context, assignment protection, exclusion reasons, and replacement rules.

Recommended build order: database schema → n8n workflow controller → landing form ingestion → one pilot county source review → one controlled sample batch → refine quality rules from real records. Do not start with a full SaaS dashboard before the first controlled batch works.

### Backend quality system for premium lead products

For a premium lead/data product, build the backend as a quality-control system before building a full SaaS dashboard. The first backend must prove:

1. where each record came from,
2. why each record made the batch,
3. whether it is assigned/reserved and protected from resale during the access period.

Use n8n as an orchestration layer, not the whole data-quality engine. n8n is good for scheduled checks, webhooks, status alerts, script triggers, manual review handoffs, and delivery notifications. Use Python/Postgres for parsing, cleaning/refining, matching, dedupe, scoring, assignment protection, and CSV/XLSX generation.

For MVP, start with one pilot county and one controlled batch before broad automation. Avoid starting with a full customer dashboard, dialer, SMS system, mobile app, or nationwide automation.

See `references/leadcurate-backend-quality-system.md` for the LeadCurate-specific backend roadmap and quality gates.

## Backend quality-first build order

When the user is building a premium lead product, treat the backend as the quality-control system, not just plumbing. Do not jump straight to a full SaaS dashboard.

First backend milestone:

1. Set up Supabase/Postgres or choose self-hosted Postgres.
2. Apply a starter schema for customers, territories, county sources, raw imports, leads, assignments, deliveries, suppression, replacement requests, and audit logs.
3. Set up n8n as the workflow controller.
4. Connect the landing page form to database/email.
5. Pick one pilot county.
6. Build a county source review.
7. Generate one sample batch.
8. Refine scoring, export columns, QA checks, and replacement rules from real records.

Backend quality must prove:

- where each record came from
- why it made the batch
- whether it is already assigned/reserved
- which quality checks it passed
- why excluded records were removed or flagged

Use n8n for orchestration: schedules, webhooks, script triggers, alerts, manual review handoffs, delivery steps. Use Python/Postgres for parsing, cleaning, matching, deduplication, scoring, export generation, and audit logging.

See `references/leadcurate-backend-quality-roadmap.md` for the session-specific backend roadmap.

## Tooling guidance

Typical early stack:

- GitHub for source of truth
- Supabase/Postgres for core data
- Python for parsing, normalization, scoring, exports
- Stripe for holds/subscriptions
- N8N or GitHub Actions for workflow orchestration
- Resend/SendGrid/Mailgun for transactional email
- Vercel/Netlify/Cloudflare Pages for landing/app hosting
- Airtable only for lightweight CRM/manual review/admin tracking, not as the main high-volume database

Use n8n as the workflow controller, not the whole data engine. n8n should schedule, trigger, notify, and hand off review/delivery steps; Python/workers should handle parsing, cleaning, matching, deduplication, scoring, and export generation. For a premium data product, quality gates and auditability matter more than a full SaaS dashboard on day one.

## Compliance boundaries

Help with compliant data workflows:

- public-record source inventory
- APIs, bulk downloads, exports, licensed data access
- DNC/opt-out/internal suppression
- source attribution and audit logs
- customer certification and disclaimers
- data quality scoring and exclusion reason codes

Do not help with:

- bypassing anti-bot protections
- rotating IPs to avoid flags
- CAPTCHA solving/evasion
- fingerprint spoofing
- scraping behind access controls
- violating site/vendor terms

When a source blocks automation, route to approved exports, APIs, permission, manual review, or alternate lawful sources.

## User-communication note

When the user is a nontechnical founder asking for setup direction, keep answers short and action-oriented. Give the exact next 2–5 steps. Avoid overloading them with architecture unless they ask for the full plan.

## Backend quality-first build order

When the user says the product must be the best quality, steer backend work toward a quality-controlled data operation before a full SaaS app. The backend must preserve source provenance, raw imports, decision context, exclusion reasons, assignment/reservation state, deliveries, replacements, and audit logs. Use n8n as the workflow controller and Python/Postgres as the data engine. Start with one pilot county and one manual-assisted sample batch before broad automation. See `references/backend-quality-system.md` for the detailed checklist.

## Customer-facing landing page copy

For premium lead/data products, do not write the landing page from the operator's internal data model. The copy must be understandable to a normal buyer who is not thinking about records, suppression, scoring, deduplication, pipelines, or schema.

When the founder intentionally includes educational “free game” (for example MAO-style deal math, offer logic, source-review education, or workflow advice), do not remove it reflexively as off-topic. Treat it as a trust-building strategy: the page gives enough process insight to show the company understands real investor work and is not hiding behind generic “motivated seller leads” hype. Keep the education concise, professional, and tied to why the data product is more valuable.

Use a two-pass copy review before telling the user the page is polished:

1. **Plain-buyer pass** — would a nontechnical investor understand what this means and why it is worth paying for?
2. **Premium-taste pass** — does it still sound professional enough for someone spending real money, without sounding childish, overly casual, or like a generic AI page?

Avoid customer-facing labels like:

- priced by effort
- data quality / quality level without concrete meaning
- flow label
- lead lanes
- routing rule
- suppress / suppressed
- active assignment window
- clean the obvious mess
- useful notes
- send the batch
- records that obviously do not belong
- what are you looking for? (on a form where intent is already clear)

Prefer clear but premium labels such as:

- Buyer profile
- Preferred access option
- County availability review
- Review the county
- Refine the records
- Add decision context
- Deliver the batch
- Source / Refine / Prioritize / Reserve / Prepare
- assigned records reserved during your active access period
- records that do not meet batch criteria

A good middle-ground tone is: simple enough to understand at a glance, but specific enough that the product does not sound like "we just clean a spreadsheet." Explain customer outcomes, not internal mechanics.

### User-specific lesson: included training without course-funnel slang

For LeadCurate-style landing pages, it is important to communicate that practical buyer education/tools are included — worksheets, call prep, follow-up structure, MAO/offer-review guidance, compliance reminders — because this differentiates the product from sellers who charge separately for basic operator training.

Do **not** phrase this as "free game" or "enough game to work the batch" on the page; the user found that wording too YouTube/course-scam sounding. Prefer professional language such as:

> We include the practical training most sellers leave out.

Then explain that the customer gets useful tools and guidance buyers often pay separate courses for, without implying guaranteed deals.

When the user is frustrated about landing-page previews or agent work proof, keep the response short and proof-forward: stable preview link, screenshot/media, commit hash, and exact path.

See `references/leadcurate-final-landing-page-lessons.md` for the session-specific final copy lessons.

## References

- Find the right records
- Clean up the list
- Limit who gets them
- Check the market
- Add useful notes
- Send the batch

When reviewing a lead/data product site, include a taste/clarity pass in addition to typo checks: ask whether every heading is readable to someone who is not technical and whether it creates immediate value for the buyer.

### Education / included-training positioning

For premium lead/data products that include worksheets, call prep, follow-up structure, MAO/offer review, or buyer education, position the value professionally. The user may describe this internally as “free game,” but on the public landing page avoid repeated slang like “game” because it can sound like a YouTube/course-funnel pitch.

Use language like:

- “practical training most sellers leave out”
- “worksheets, call prep, follow-up structure, and offer-review guidance”
- “included tools buyers often pay separate courses for”
- “helps buyers understand why a record is worth reviewing without pretending the data closes deals by itself”

Keep the competitive edge, but do not over-hype it. The landing page should feel premium and trustworthy; sharper/aggressive messaging can be saved for ads and commercials.

For frustrated or skeptical users, do not keep explaining process in long replies. Verify with a concrete artifact (preview URL, screenshot, commit hash, or exact file path), answer briefly, then act.

## References

- `references/leadcurate-case-study.md` — condensed case study from a premium property/deed lead product planning session, including pricing, offer structure, territory logic, and MVP recommendations.
- `references/leadcurate-case-study.md` — condensed case study from a premium property/deed lead product planning session, including pricing, offer structure, territory logic, and MVP recommendations.
- `references/leadcurate-backend-quality-model.md` — backend operating model for building LeadCurate as a quality-controlled data operation before a full SaaS dashboard.
- `references/leadcurate-copy-calibration.md` — customer-facing copy lessons for LeadCurate: avoiding internal data jargon without becoming too casual or elementary.
- `references/leadcurate-landing-copy-taste.md` — session-specific copy taste notes for making LeadCurate landing-page labels readable to nontechnical buyers without sounding childish or generic.
- `references/leadcurate-strategic-vision.md` — LeadCurate-specific strategic positioning: educational “free game,” anti-scam trust posture, concrete product workflow, and realistic commercial direction.

- `references/leadcurate-backend-quality-system.md` — backend roadmap for LeadCurate's quality-control system: Postgres, n8n orchestration, Python processing, pilot county workflow, quality gates, and export fields.
- `references/leadcurate-backend-quality-roadmap.md` — quality-first backend build order for LeadCurate: Postgres/Supabase, n8n orchestration, Python data processing, auditability, and sample-batch-first validation.
- `references/leadcurate-strategic-positioning.md` — LeadCurate positioning notes: why educational “free game” and MAO-style context can be strategic, how to avoid scammy lead-seller claims, and what operating workflow to make explicit.
