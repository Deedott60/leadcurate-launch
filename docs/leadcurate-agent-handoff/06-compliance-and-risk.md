# 06 - Compliance And Risk

This is not legal advice. The legal pages and policies must be reviewed before production.

## Claims to avoid

Avoid:

- guaranteed deals
- guaranteed motivated sellers
- safe to call
- exclusive if not actually exclusive
- every record has contact data
- AI predicts who will sell
- customers can ignore compliance

Use:

- DNC-aware fields where applicable
- contact data where available
- source dates included
- score reasons included
- customer handles outreach, compliance, verification, negotiation, and closing

## Public source rules

Allowed:

- official public-record portals
- public CSV/PDF/report downloads
- normal browser navigation of public pages
- preserving source URL, source date, and access notes

Avoid:

- bypassing CAPTCHAs
- bypassing logins/paywalls
- evading anti-bot controls
- ignoring terms/access restrictions
- scraping restricted records
- reselling data without source review

## DNC/contact policy

Default policy:

- do not skip trace raw records
- enrich only records that pass dedupe, suppression, and quality checks
- run DNC/contact suppression after enrichment
- if suppression provider fails, do not export contact fields
- keep non-contact property record if otherwise valid
- mark DNC/contact status clearly

Do not tell customers a number is safe to call.

## Sample batch safety

For unpaid previews:

- 10-25 rows is enough
- include source dates and score reasons
- contact fields can remain `not_enriched`
- optionally blur owner/contact fields
- include compliance disclaimer

Recommended disclaimer:

> Sample records are public-record-derived and DNC-aware where applicable. Buyer is responsible for verifying records, outreach compliance, licensing obligations, and transaction decisions.

## Legal pages

Current template pages:

- `site/terms.html`
- `site/privacy.html`
- `site/refund-policy.html`
- `site/compliance.html`

These contain placeholders and must be reviewed.
