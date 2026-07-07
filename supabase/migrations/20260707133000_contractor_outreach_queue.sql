create table if not exists public.contractor_outreach_queue (
  id uuid primary key default gen_random_uuid(),
  source text not null default 'nyc_dob_active_licenses',
  lane text not null default 'nyc_code_violations',
  firm_name text,
  contact_name text,
  email text not null,
  phone text,
  license_type text,
  license_number text,
  business_city text,
  business_state text,
  business_zip text,
  trade text,
  territory text,
  sample_url text not null default 'https://leadcurate.com/sample-deliveries/nyc-code-violations-2026-07-06/',
  status text not null default 'queued',
  first_sent_at timestamptz,
  follow_up_due_at timestamptz,
  follow_up_sent_at timestamptz,
  reply_status text,
  last_error text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists contractor_outreach_email_lane_uidx
  on public.contractor_outreach_queue (lower(email), lane);

create index if not exists contractor_outreach_status_due_idx
  on public.contractor_outreach_queue (status, follow_up_due_at, created_at);

alter table public.contractor_outreach_queue enable row level security;

revoke all on public.contractor_outreach_queue from anon, authenticated;
grant all on public.contractor_outreach_queue to service_role;

comment on table public.contractor_outreach_queue is
  'Manual-trigger contractor outreach queue. NYC DOB license contacts are queued here; n8n sends at operator-controlled cadence only.';
