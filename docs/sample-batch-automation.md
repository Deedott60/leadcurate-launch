# LeadCurate Sample Batch Automation

This is the no-spend workflow for making a legitimate sample batch within a day.

## What this does

The starter script `scripts/build_sample_batch.py` turns a lawful public-record CSV into a LeadCurate sample file.

It:

- reads a public-record CSV
- maps common owner, address, parcel, date, and balance columns
- deduplicates by owner/property/parcel/source
- assigns a simple score and score reason
- marks contact status as `not_enriched`
- marks DNC status as `not_scrubbed`
- exports a buyer-facing sample CSV
- creates a blank sales call tracker

It does not:

- scrape blocked websites
- bypass logins, paywalls, CAPTCHAs, or anti-bot controls
- skip trace records
- DNC scrub phone numbers
- claim any phone number is safe to call

## Why this is still valuable

Yes, a motivated buyer could hunt for raw public records on their own. The value is that most buyers do not want to:

- find the right county source
- understand which source is stale or useful
- clean messy owner/property fields
- dedupe repeated records
- classify the lead lane
- preserve source dates
- score why a record deserves review
- package it into a workflow-ready CSV
- avoid buying the same exhausted list everyone else has

LeadCurate should sell the cleaned, scored, source-backed, limited-seat workflow, not the idea that public records are secret.

## Freshness strategy

For samples, use the freshest source file available from the county.

For paid seats:

- County Seat: monthly pull/update
- Operator Seat: biweekly target where source volume supports it
- Exclusive Territory: weekly or biweekly if the source updates often enough

If a county source only updates monthly, do not claim weekly freshness. The honest promise is source-dated data, not fake freshness.

## First sample command

Download a lawful public-record CSV from a county source, then run:

```powershell
py -3.11 scripts\build_sample_batch.py `
  --input .\data\raw\sample-county-source.csv `
  --output .\data\exports\sample-batch.csv `
  --county "Mecklenburg" `
  --state NC `
  --source-type "tax delinquent" `
  --source-url "https://example-county-source.gov/source-page" `
  --source-date "2026-06-13" `
  --limit 50
```

## Sales call positioning

Use this wording:

> I pulled a small source-backed sample for this county and cleaned it into a review-ready batch. It includes source dates, lead category, score reason, and contact/DNC fields marked as not enriched yet. If the county looks useful, the paid review checks volume and seat availability before I sell access.

Avoid:

> These are guaranteed motivated sellers.

Avoid:

> These numbers are safe to call.

Avoid:

> Nobody else can get this.

Better:

> The raw records may be public. The value is the cleaning, dedupe, scoring, source context, and limited-seat delivery.

## Day-one process

1. Pick one county.
2. Pick one lane: tax delinquent, foreclosure, probate, absentee, vacancy, or code violation.
3. Find an official public source.
4. Download a CSV/PDF/report if the source offers it.
5. Convert PDF/report to CSV manually if needed.
6. Run `scripts/build_sample_batch.py`.
7. Review the output manually.
8. Remove weak or questionable rows.
9. Call local investors/wholesalers with the sample.
10. Sell the $175 county review deposit before promising a full seat.
