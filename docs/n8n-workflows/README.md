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
