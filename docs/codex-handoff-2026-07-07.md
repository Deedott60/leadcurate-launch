# Codex Handoff — 2026-07-07 (supersedes 07-06 items 1-4, all done ✅)

## 1. Executive-report delivery email (Derrick-approved direction)
Upgrade the send-delivery email into a premium intelligence briefing. Structure, top to bottom:
- Opportunity headline: "196 Active Code Violations Ready for Investor Outreach — Est. Property Value $4.49M. Delivered today. Cleaned, verified, ready to market."
- Stat row: total records · avg property value · median years held · mailing-address coverage · download button
- One-page summary paragraph + "Working notes"
- Suggested outreach strategy line (e.g. "avg 14 yrs held → direct mail first contact")
- 5-row sample table (unredacted, it's paid)
- **Upsell block** ("Available today: ✅ Verified Vacant Land ✅ Absentee ✅ Out-of-State ✅ Tax Delinquent ✅ Asset Locator ✅ County Intelligence") with sample-page links
- Brand: cream/navy/emerald only. Build as reusable template in the delivery pipeline.

## 2. n8n contractor outreach workflow (manual-trigger ONLY per locked rule)
- Source: NYC DOB licensed-contractor public lists (facade/masonry/boiler trades) → firm name, email
- Queue in Supabase (new table ok, RLS on), dedupe by email
- Send via Hostinger Mail API from hello@leadcurate.com: **max 5-6/hour**, template from `docs/outreach/b2b-lanes-2026-07-06.md` Lane 2 + sample link `https://leadcurate.com/sample-deliveries/nyc-code-violations-2026-07-06/`
- 3-day no-reply follow-up step. Log sends to activity_feed. NO auto-activation — Derrick triggers.

## 3. Nationwide verified-vacant
Refactor `scripts/leadcurate/process_verified_vacant.py`: per-county column map (vacant flag, land/bldg value, yearbuilt, heatedarea, owner, acreage). Target next: Wake NC, Guilford NC, Fulton GA, Marion IN (parcel files on disk). Same six checks, same triple output.

## 4. Soft-open pricing (Derrick delegated; bake into tiers page + quote templates, NOT public landing)
Tier 4 Curated Distress $149 ($99 first 5) · Tier 3 Breaking Point $249 · Tier 2 Fresh Triggers $199/mo · Tier 1 Auction Hot Sheet $497 · Tier 5 Ground Floor $299/report · Verified Vacant $149/county · Contractor cut $199 borough-class / $349 citywide · Asset Locator $750 file / $1,500 custom book.
Landing page stays quoted-with-preview + waitlist (public prices only after Derrick's final confirm).

## 5. Landing page: remove/hide annual billing toggle (unproven pricing), keep waitlist labels.

Report each item via conf:done.
