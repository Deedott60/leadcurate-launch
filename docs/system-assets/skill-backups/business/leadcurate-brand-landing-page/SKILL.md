---
name: leadcurate-brand-landing-page
description: Use when editing or reviewing LeadCurate landing-page copy, positioning, visuals, or offer structure. Preserves Derrick's trust-first county property data strategy and avoids re-learning the brand vision.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [leadcurate, landing-page, copywriting, data-product, real-estate]
    related_skills: [lead-data-product-planning]
---

> ⚠ **READ `/CLAUDE.md` AT THE REPO ROOT FIRST.** This skill is HISTORICAL (pre-2026-06-23). The current brand voice, 4-tier system, customer flow, visual brand kit, and reference files are in CLAUDE.md.
>
> **What's outdated below:**
> - Landing page references at `/site/` — PARKED. Front door is intake form + packages page now.
> - Pricing ladder (County Review Deposit / County Seat / Operator Seat / Exclusive Territory) — DEAD. Replaced by 4-tier system in CLAUDE.md §3.
> - Nginx preview path `/var/www/leadcurate-preview` — STALE. Live pages on GitHub Pages.
> - "Landing page structure 1-8" section — describes parked page. See `docs/packages/index.html` for current customer-facing tier overview.
>
> **What's still valid:**
> - Brand palette (cream / dark slate / emerald / serif headlines) — still our colors.
> - Tone rules (premium, grounded, transparent, no hype, no guaranteed-deal language) — still locked.
> - "What makes it different" list — still our differentiation.
> - Anti-scammy wording rules (no "free game", no "safe to call") — still locked.
>
> For ALL current LeadCurate work, CLAUDE.md is the source of truth.

# LeadCurate Brand + Landing Page Workflow

## Overview

Use this skill whenever working on LeadCurate copy, landing pages, ads, commercials, product briefs, or handoffs. Derrick does not want agents to repeatedly rediscover the business vision.

LeadCurate is a premium county-based property data product for serious real estate investors. It should not feel like a generic lead seller, a spam shop, or a hype course funnel.

## Core positioning

LeadCurate reviews county source records first, then cleans, dedupes, scores, and delivers limited-seat batches with source context.

Strong short positioning:

> Limited-seat county property data for serious investors.

Current final landing-page hero direction:

> Stop buying the same stale property lists everyone else is working.

Supporting idea:

> LeadCurate reviews county source records first, then cleans, dedupes, scores, and delivers limited-seat batches with source dates, score reasons, contact data where available, and DNC-aware fields where applicable.

## What makes it different

The market has a trust problem. Many lead companies oversell stale records, hide the process, and imply results they cannot guarantee. LeadCurate should win by being precise and transparent:

- review county source availability before selling access
- explain usable record volume and buyer-seat capacity
- clean and dedupe records
- preserve source/review dates
- include score or priority reasons
- include contact data where available
- include DNC-aware fields where applicable
- protect assigned records from broad resale during the active access period
- give buyers practical worksheets/tools so they can work the batch properly

## Education/training angle

Derrick wants to communicate that LeadCurate includes practical training/tools buyers often pay separate courses for. Do not use repeated slang like “free game” on the page because it can sound YouTube-scammy.

Preferred wording:

> We include the practical training most sellers leave out.

Supporting copy:

> LeadCurate includes the worksheets, call prep, follow-up structure, and offer-review guidance buyers often pay separate courses for — without pretending the data closes deals by itself.

## Tone rules

Use:

- premium, grounded, trustworthy language
- plain investor-facing language
- precise compliance-aware caveats
- direct contrast with stale/mystery lists
- “review”, “refine”, “decision context”, “county availability”, “limited seats”
- enough competitive edge to show LeadCurate includes practical training/tools buyers often pay separate courses for

Avoid:

- “guaranteed deals”
- “guaranteed motivated sellers”
- “safe to call/text”
- implying all records include contact data
- implying all outreach is compliant
- repeated “free game” phrasing
- too much technical/internal jargon like lead lanes, suppression windows, routing logic, priced by effort

## Current accepted brand palette / design direction

Keep the existing landing-page palette and visual direction:

- cream background
- dark slate/navy panels
- emerald accents
- premium serif headlines
- rounded cards
- clean, operational dashboard mockup

Do not make it louder or more colorful just to sound aggressive. Use ads/commercials for higher energy.

## User feedback / copy calibration

Derrick disliked the phrase “enough game to work the batch correctly” because it sounded YouTube-scammy. But he still wants the page to communicate that LeadCurate gives buyers practical materials that other courses may charge heavily for. Use professional wording like “practical training,” “worksheets,” “call prep,” “follow-up structure,” and “offer-review guidance.” Avoid removing the competitive value entirely; do not over-soften the page.

## Landing page structure to preserve

1. Hero: stale-list problem + limited-seat county property data.
2. Trust section: review source, refine records, limit seats.
3. Education section: practical training/tools most sellers leave out.
4. Dark process section: source → refine → prioritize → reserve → prepare.
5. Pricing: county review, county seat, operator seat, exclusive territory.
6. What you receive: clean file, source/review date, score reason, assignment ID, contact/DNC fields where applicable, MAO/offer worksheet, call prep/compliance reminders.
7. County availability form.
8. FAQ: seats, deliverables, exclusivity, same records, no guarantee, contact data availability.

## Canonical repo and preview

- Repo path on VPS: `/root/leadcurate-launch`
- Static page: `/root/leadcurate-launch/site/index.html`
- Current Hostinger/VPS preview: `http://76.13.25.117/leadcurate-preview/`
- Nginx static preview folder: `/var/www/leadcurate-preview`

After editing `site/index.html`, update preview:

```bash
rm -rf /var/www/leadcurate-preview
mkdir -p /var/www/leadcurate-preview
cp -a /root/leadcurate-launch/site/. /var/www/leadcurate-preview/
chmod -R a+rX /var/www/leadcurate-preview
```

Verify:

```bash
curl -I --max-time 10 http://76.13.25.117/leadcurate-preview/
```

## Verification checklist

- [ ] Copy does not sound scammy or hypey.
- [ ] Contact data says “where available.”
- [ ] DNC fields say “where applicable.”
- [ ] No guaranteed deal language.
- [ ] CTA language is consistent: “Check county availability” and “View pricing.”
- [ ] The practical training/tool value is present without using “free game” slang repeatedly.
- [ ] Preview updated and returns 200 OK.
- [ ] Changes committed and pushed to GitHub.
