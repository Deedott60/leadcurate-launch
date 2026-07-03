# LeadCurate n8n Workflows

These exports document the workflows installed in Derrick's n8n instance at the time they were created. Secrets are stored in n8n credentials or server env, not in these files.

## intake_router

- Workflow id: `J4UINOlYYNPPlpGi`
- Trigger: schedule, every 1 minute
- Purpose: route new `intake_requests` into a recommended LeadCurate tier.
- Steps:
  1. Fetch untriaged rows from Supabase where `routed_at is null`.
  2. Apply the locked LeadCurate tier-picker logic.
  3. Call `public.route_intake_recommendation(...)` with the n8n router header credential.
  4. Supabase enriches the intake and linked prospect, then posts `intake:triaged` to `activity_feed`.

## Credentials

- `LeadCurate Router Secret Header`: guarded Supabase RPC calls.
- `LeadCurate OpenRouter Bearer`: reserved for AI triage workflows.
- `LeadCurate Hostinger Mail Bearer`: reserved for Agentic Mail workflows.

Native Supabase service-role credentials were not created because no Supabase service-role key is present in the shared VPS env or `private.app_secrets`. Workflow 1 uses the existing dashboard-safe publishable-key path plus a guarded RPC.

## Test

The live queue was empty when this workflow was installed, so no fake intake was inserted. To test with real behavior, submit one normal intake form entry and confirm within 60 seconds:

- `intake_requests.recommended_tier` is populated.
- The linked `prospects` row has `intake_request_id` and `recommended_tier`.
- `activity_feed` has an `intake:triaged` event from `n8n`.

## manual_delivery_pipeline

- Export: `leadcurate_manual_delivery_pipeline.json`
- Live workflow id: `UXqcRtvkOSY8Dcmn`
- Trigger: manual only. The workflow is intentionally inactive and has no cron/webhook trigger.
- Purpose: orchestrate a requested market + lane into a verified delivery package.
- Steps:
  1. Operator edits the Manual inputs node (`market`, `lane`, `count`, `allow_scrape`).
  2. POST to the protected host runner at `http://172.18.0.1:8788/run`, which executes `/opt/leadcurate/scripts/leadcurate_pipeline.py` on the VPS.
  3. Run an OpenRouter LLM quality decision node for edge cases and source-signal judgment.
  4. Pass through a no-op `Payment approval placeholder`.
  5. Post `delivery:ready_to_send` or `delivery:needs_review` to `activity_feed`.

## ground_floor_manual

- Export: `leadcurate_ground_floor_manual.json`
- Live workflow id: `eToSdkvZxBRWLNmm`
- Trigger: manual only. The workflow is intentionally inactive and has no cron/webhook trigger.
- Purpose: manually scan/refresh $200M+ investment signals and package one county's investment signal + parcel data for Claude review.
- Steps:
  1. Operator edits the Manual inputs node (`market`, default `guilford-nc`).
  2. POST to the protected host runner to execute `/opt/leadcurate/scripts/ground_floor_pipeline.py scan-investments`.
  3. Run an OpenRouter LLM decision node to confirm source confidence.
  4. POST to the protected host runner to execute `/opt/leadcurate/scripts/ground_floor_pipeline.py package-county --market <market>`.
  5. Post `ground_floor:ready_for_review` or `ground_floor:needs_review` to `activity_feed`.

The protected host runner is installed as `leadcurate-n8n-runner.service`, bound to Docker bridge `172.18.0.1:8788`, and UFW allows that port only from `172.18.0.0/16`. n8n authenticates with the encrypted `LeadCurate Runner Header` credential. OpenRouter calls use the encrypted `LeadCurate OpenRouter Bearer` credential, not container env vars.

Ground Floor writes through the narrow Supabase RPCs `upsert_ground_floor_investments(...)` and `insert_ground_floor_county_package(...)`. The VPS sends its existing `N8N_API_KEY`; Supabase stores only the SHA-256 hash in `private.app_secrets`, so the workflow can write these two Ground Floor tables without exposing a service-role key in n8n.

Known source/data blockers:

- `duval-fl` and `davidson-tn` are valid pipeline market slugs now, but no raw files or scrape source URLs are registered yet. With `--allow-scrape`, the pipeline routes both to `scrape_dispatcher` and returns a source-needed blocker instead of fabricating data.
- `tarrant-tx` and `maricopa-az` have raw ZIP files, but need extractor modules before delivery.
- `shelby-tn` has a raw tax-sale CSV, but the current parser builds zero deliverable owner records and needs parser work or source review.
- `jefferson-ky/code-violations` has violation/source rows but lacks owner/value columns in the tested source, so it correctly routes to review instead of fabricating a list.

## Manual-trigger rule

The two new workflows above must stay inactive/manual until Derrick explicitly asks to activate an automated trigger. Do not add Schedule Trigger, live webhook, or cron behavior to them without a new direct instruction.
