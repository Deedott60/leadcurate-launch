-- LeadCurate starter Supabase/Postgres schema
-- Draft v0.1. Review before production use.

create table if not exists customers (
  id uuid primary key default gen_random_uuid(),
  name text,
  email text not null,
  phone text,
  company text,
  investor_type text,
  status text not null default 'prospect',
  stripe_customer_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists territories (
  id uuid primary key default gen_random_uuid(),
  state text not null,
  county text not null,
  zone_name text,
  territory_type text not null default 'county',
  territory_score integer,
  flow_label text,
  expected_monthly_min integer,
  expected_monthly_max integer,
  max_seats integer default 1,
  active_seats integer default 0,
  exclusive_available boolean default true,
  status text not null default 'research',
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (state, county, territory_type)
);

create table if not exists county_sources (
  id uuid primary key default gen_random_uuid(),
  territory_id uuid references territories(id) on delete cascade,
  source_name text not null,
  source_type text not null,
  source_url text,
  access_method text,
  refresh_cadence text,
  terms_notes text,
  parser_status text default 'not_started',
  reliability_score integer,
  created_at timestamptz not null default now()
);

create table if not exists raw_imports (
  id uuid primary key default gen_random_uuid(),
  territory_id uuid references territories(id) on delete set null,
  source_id uuid references county_sources(id) on delete set null,
  import_type text,
  source_date date,
  pulled_at timestamptz not null default now(),
  file_url text,
  file_hash text,
  record_count integer,
  status text not null default 'imported',
  notes text
);

create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  raw_import_id uuid references raw_imports(id) on delete set null,
  territory_id uuid references territories(id) on delete set null,
  state text,
  county text,
  zip_code text,
  zone_name text,
  owner_name text,
  property_address text,
  mailing_address text,
  parcel_id text,
  property_type text,
  owner_type text,
  owner_entity_type text,
  source_type text,
  source_date date,
  distress_type text,
  lead_lane text,
  record_tags text[],
  phone text,
  phone_type text,
  email text,
  dnc_status text,
  scrubbed_at timestamptz,
  skip_trace_confidence numeric(5,2),
  urgency_level integer,
  lead_score integer,
  score_reason text,
  resale_eligibility text default 'eligible',
  suppression_status text default 'active',
  google_maps_url text,
  assessor_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists territory_rights (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid references customers(id) on delete cascade,
  territory_id uuid references territories(id) on delete cascade,
  territory_type text not null default 'county',
  zip_codes text[],
  lead_lane text,
  exclusivity_type text not null default 'limited_seat',
  seat_number integer,
  start_date date,
  end_date date,
  expected_monthly_min integer,
  expected_monthly_max integer,
  suppression_rule text,
  status text not null default 'active',
  created_at timestamptz not null default now()
);

create table if not exists lead_assignments (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid references leads(id) on delete cascade,
  customer_id uuid references customers(id) on delete cascade,
  territory_right_id uuid references territory_rights(id) on delete set null,
  assigned_at timestamptz not null default now(),
  exclusivity_window_start timestamptz not null default now(),
  exclusivity_window_end timestamptz,
  status text not null default 'assigned',
  unique (lead_id, customer_id)
);

create table if not exists deliveries (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid references customers(id) on delete cascade,
  territory_id uuid references territories(id) on delete set null,
  lead_lane text,
  delivery_date date not null default current_date,
  lead_count integer default 0,
  file_url text,
  status text not null default 'draft',
  created_at timestamptz not null default now()
);

create table if not exists delivery_leads (
  delivery_id uuid references deliveries(id) on delete cascade,
  lead_id uuid references leads(id) on delete cascade,
  primary key (delivery_id, lead_id)
);

create table if not exists replacement_requests (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid references customers(id) on delete cascade,
  lead_id uuid references leads(id) on delete set null,
  reason text not null,
  status text not null default 'open',
  resolution text,
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create table if not exists suppression_records (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid references leads(id) on delete cascade,
  suppression_type text not null,
  reason text,
  starts_at timestamptz not null default now(),
  ends_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor text,
  action text not null,
  entity_type text,
  entity_id uuid,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_leads_territory on leads(territory_id);
create index if not exists idx_leads_county_lane on leads(state, county, lead_lane);
create index if not exists idx_leads_score on leads(lead_score desc);
create index if not exists idx_assignments_lead on lead_assignments(lead_id);
create index if not exists idx_assignments_customer on lead_assignments(customer_id);
