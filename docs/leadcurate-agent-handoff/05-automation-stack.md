# 05 - Automation Stack

## Recommended stack

- Vercel: static landing page
- Supabase: Postgres database and possibly Storage
- n8n: workflow controller
- Python scripts: parsing, cleaning, scoring, exports
- Resend/SendGrid/Mailgun: email alerts and delivery links
- Stripe: deposits, single batches, subscriptions

## Supabase responsibilities

Supabase should store:

- customers
- territories
- county sources
- raw imports
- leads
- lead assignments
- deliveries
- replacement requests
- suppression records
- audit logs
- intake requests
- workflow runs/events
- lead exclusions
- quality checks

Starter schema:

- `supabase/schema.sql`

Missing workflow tables are specified in:

- `docs/leadcurate-v1-n8n-spec.md`

## n8n responsibilities

n8n should:

- trigger scheduled county pulls
- call scripts
- route failures
- send alerts
- move records to manual review
- send delivery emails or links
- write workflow run status

n8n should not be the full data engine.

## Python responsibilities

Python should:

- read source files
- normalize fields
- dedupe
- classify lanes
- score records
- generate exports
- create sample batches

Current starter script:

- `scripts/build_sample_batch.py`

## Intake form path

Best path:

1. Landing page form submits to a server/API endpoint.
2. Endpoint writes to Supabase `intake_requests`.
3. Endpoint sends email notification to owner.
4. Intake status moves through `new`, `reviewing`, `quoted`, `deposit_sent`, `active`, `closed_lost`.

Formspree/Web3Forms is optional and should only be used as a short-term shortcut.

## Go-live backend minimum

Before taking live deposits:

- Supabase table for intake exists
- form endpoint works
- email alert works
- Stripe deposit link exists
- source review status can be tracked
- legal pages have business placeholders replaced
