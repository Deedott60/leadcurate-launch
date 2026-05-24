---
name: data-product-launch
description: "Launch premium data products from messy sources: offer strategy, trust positioning, MVP stack, pricing, schema, and go-to-market."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [data-products, launch, pricing, mvp, landing-page, compliance, lead-products]
---

# Data Product Launch

Use this skill when helping a founder turn messy data sources into a sellable premium data product: lead intelligence, market intelligence, public-record products, curated datasets, enriched CSV delivery, or an MVP data subscription.

The default posture is **operator-first and execution-oriented**: simplify the offer, reduce buyer confusion, build a working foundation, and avoid hype.

## Core positioning pattern

For premium data products, position around the transformation and trust layer:

> We turn messy source data into cleaned, classified, scored, auditable, buyer-ready data.

Good product language:

- better data, cleaner workflow, no hype
- source-attributed data
- quality filters before quantity promises
- limited access / territory / segment rights when applicable
- confidence scoring and reason codes
- clear exclusions and replacement rules
- practical operating tools included

Avoid:

- guaranteed outcomes
- secret-data claims
- hype/guru positioning
- cheap commodity list language
- overloading the public page with every upsell

## Founder workflow

1. **Extract the plan**
   - Read the business plan or notes.
   - Identify the core data transformation, buyer, offer, and proof needed.

2. **Simplify the offer**
   - Reduce public pricing to 3–4 clear choices.
   - Keep add-ons/custom packages as sales-call or later-stage language.
   - Name the entry product in terms of the buyer's purpose, not internal operations.

3. **Define the data moat**
   - Source inventory
   - Ingestion method
   - Cleaning/parsing requirements
   - Deduplication logic
   - Enrichment and validation
   - Suppression/exclusion logic
   - Confidence/quality scoring
   - Delivery/audit logs

4. **Build MVP foundation**
   - Landing page or prototype
   - Repo/docs source of truth
   - Starter database schema
   - Sample CSV/export format
   - Simple intake form
   - Payment flow plan
   - Manual QA loop before automation

5. **Protect trust**
   - Explain what is and is not guaranteed.
   - Show sample data with sensitive fields blurred.
   - Use source dates, confidence labels, replacement policy, and compliance reminders.

## Pricing simplification pattern

For a new premium data subscription, start with a simple ladder:

1. **Review/Deposit** — low-friction paid validation, credited forward if activated.
2. **Standard Seat** — core monthly subscription.
3. **Operator/Pro Seat** — higher volume, priority, or more frequent delivery.
4. **Exclusive/Custom** — high-ticket quote after source/volume audit.

Do not lead with per-record pricing if scarcity, quality, and workflow are the real value. Per-record pricing commoditizes the product and attracts bargain buyers.

## Unit economics sanity check

Separate costs into:

- variable per-record cost: enrichment, validation, DNC/status checks, data utilities
- fixed per-territory or per-source cost: setup, parser maintenance, QA, support, source monitoring
- founder/operator time: the hidden early-stage cost

Rule of thumb: **clean first, enrich second**. Do not pay to enrich junk records.

## Delivery cadence

Avoid expensive near-real-time enrichment until a buyer pays for it.

Recommended MVP sequence:

1. Pull/source data.
2. Clean and dedupe.
3. Score/classify.
4. Approve records for delivery.
5. Enrich approved records only.
6. Apply suppression/compliance fields.
7. QA.
8. Deliver CSV/XLSX or signed file link.

## Trust-building education

If the market is full of expensive courses or hype, give away the generic operating basics and sell the hard data product.

Good included/free resources:

- call prep sheets
- calculators
- batch trackers
- follow-up calendars
- checklists
- template libraries
- compliance reminders
- first-batch action plans

Do not copy another course, manual, or proprietary materials. Recreate general workflows in original language.

## MVP tech stack

Default early stack:

- GitHub: code/docs source of truth
- Supabase/Postgres: database and storage
- Stripe: deposits/subscriptions
- Vercel/Netlify/Cloudflare Pages: landing/app hosting
- n8n/GitHub Actions/Python: automation and data processing
- Resend/SendGrid/Mailgun: transactional delivery
- CSV/XLSX: first deliverable
- Airtable only for lightweight ops/review, not the main warehouse at scale

## When building immediately

If the user says to start executing and GitHub access exists:

1. Create a private repo.
2. Add `README.md`, `docs/product-strategy.md`, `docs/data-platform.md`, `supabase/schema.sql`, and a landing page/prototype.
3. Commit and push.
4. Verify the page or files before reporting success.

## Reference files

- `references/property-lead-intelligence.md` — details from a LeadCurate-style property/deed lead intelligence launch: limited-seat counties, DNC-status language, Operator Kit, lead lanes, and first schema concepts.
