# LeadCurate Data Platform Plan

## MVP architecture

Use a manual-assisted data product first, not a full SaaS platform.

- Landing page: static/Next.js/Vercel later
- Payments: Stripe
- Database: Supabase Postgres
- Automation: n8n
- Email: Resend/SendGrid/Mailgun
- Data processing: Python scripts
- Delivery: CSV/XLSX via email or signed storage link
- Admin review: Supabase table editor or Airtable-style review later

## Lead source workflow

For each county:

1. Identify lawful public-record sources.
2. Record source URL, source type, refresh cadence, terms/access notes.
3. Pull sample data for 60–90 days where possible.
4. Count raw records by source and lead lane.
5. Normalize addresses, parcel IDs, owner names, and source dates.
6. Deduplicate by owner-property-source-event logic.
7. Classify owner type and property type.
8. Score territory flow.
9. Decide seat count: 1, 2, 3, exclusive-only, bundle-only, or do-not-sell.

## Lead processing workflow

1. Ingest raw import.
2. Preserve raw source file and metadata.
3. Parse into normalized lead candidates.
4. Deduplicate.
5. Suppress already-assigned, duplicate, stale, risky, or restricted records.
6. Classify lead lane.
7. Score urgency and quality.
8. Approve records for enrichment.
9. Skip trace only approved records.
10. Mark DNC/status where applicable.
11. QA batch.
12. Assign to customer.
13. Generate CSV/XLSX.
14. Log delivery.

## Lead lanes

- residential_distress
- absentee_owner
- tax_delinquent
- probate_estate
- foreclosure
- code_violation
- lien_judgment
- vacant_property
- commercial
- land_vacant
- reo_bank_owned
- nurture
- research_only
- suppressed

## Quality rule

Do not call a record bad just because it is not right for the main residential buyer. Route it correctly:

- premium lead
- specialty lead
- nurture lead
- research-only
- suppressed/do-not-sell

## Replacement policy logic

Replace only if:

- duplicate delivered inside same customer batch
- wrong county/territory/lane
- missing required field that should have been included
- clear parsing error
- record already assigned during an active exclusivity window
- contact data failed the stated quality standard

Do not replace because:

- seller was not motivated
- seller did not answer
- buyer did not close
- property was not a deal
- customer failed to follow up

## Future differentiators

Possible upsells after MVP:

- comparable-property snapshot
- Google Maps/property view links
- parcel/assessor links
- custom buyer branded mail/email kits
- direct mail partner integration
- CRM export formats
- weekly priority hotlist
- commercial corridor lead lane
- county/zip exclusivity locks

## Google Maps/property links

Useful low-cost differentiator:

- Google Maps search link from property address
- county GIS/parcel link where available
- street-view style property review link where available
- assessor property record link where available

Do not make map links a launch blocker. Add as a field in exports when easy.

## Compliance posture

LeadCurate provides data and education only. Customers are responsible for outreach, dialing, texting, mailing, contracts, licensing obligations, and compliance with federal, state, and local law.

Avoid saying "safe to call." Say "DNC-status marked" or "DNC-aware fields included."
