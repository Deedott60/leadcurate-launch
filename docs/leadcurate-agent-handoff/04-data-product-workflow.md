# 04 - Data Product Workflow

## Product workflow

1. Select one county and one source lane.
2. Record the source URL, source date, access method, and terms/access notes.
3. Pull a lawful source file manually first.
4. Preserve raw file before cleaning.
5. Normalize owner/property/parcel/source fields.
6. Deduplicate.
7. Classify lead lane.
8. Score records.
9. Exclude weak, duplicate, wrong-county, stale, or restricted records.
10. Skip trace only approved records when provider is configured.
11. DNC/contact scrub after enrichment.
12. QA manually.
13. Export CSV/XLSX.
14. Assign records to a customer and protect during active access window.
15. Log delivery and audit decisions.

## Sample batch workflow

The no-spend sample path uses `scripts/build_sample_batch.py`.

Input:

- a CSV downloaded from a lawful public source

Output:

- buyer-facing sample batch CSV
- sales call tracker CSV

Example:

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

## Sample batch columns

- assignment preview ID
- owner name
- property address
- mailing address
- parcel ID
- county/state
- lead lane
- source type
- source date
- score
- score reason
- contact status
- DNC status
- source URL
- notes

## Freshness policy

Do not fake freshness.

- If the county source updates weekly, LeadCurate can offer weekly/biweekly review.
- If the county source updates monthly, LeadCurate should promise monthly source-dated updates.
- If the source is stale, mark it as stale and do not oversell the county.

## Value statement

The customer is not paying because the raw record is impossible to find. They are paying because LeadCurate turns messy records into a repeatable, source-backed, buyer-ready operating file.
