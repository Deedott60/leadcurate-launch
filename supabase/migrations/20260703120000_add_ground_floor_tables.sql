create table if not exists public.ground_floor_investments (
  id uuid primary key default gen_random_uuid(),
  location text not null,
  state text,
  county text,
  company text not null,
  dollar_amount numeric,
  dollar_amount_text text,
  job_count integer,
  announcement_date date,
  project_stage text,
  source_url text not null,
  second_source_url text,
  confidence_level text not null default 'medium'
    check (confidence_level in ('high', 'medium', 'low')),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (location, company, announcement_date, source_url)
);

create table if not exists public.ground_floor_county_packages (
  id uuid primary key default gen_random_uuid(),
  market_slug text not null,
  county text,
  state text,
  investment_id uuid references public.ground_floor_investments(id) on delete set null,
  investment_snapshot jsonb not null default '{}'::jsonb,
  property_snapshot jsonb not null default '{}'::jsonb,
  package_path text,
  source_files text[] not null default '{}',
  status text not null default 'ready_for_review',
  created_at timestamptz not null default now()
);

create index if not exists idx_ground_floor_investments_location
  on public.ground_floor_investments (state, county, announcement_date desc);

create index if not exists idx_ground_floor_investments_amount
  on public.ground_floor_investments (dollar_amount desc nulls last);

create index if not exists idx_ground_floor_county_packages_market
  on public.ground_floor_county_packages (market_slug, created_at desc);

alter table public.ground_floor_investments enable row level security;
alter table public.ground_floor_county_packages enable row level security;

grant select, insert, update, delete on public.ground_floor_investments to service_role;
grant select, insert, update, delete on public.ground_floor_county_packages to service_role;
grant select on public.ground_floor_investments to authenticated;
grant select on public.ground_floor_county_packages to authenticated;

drop policy if exists "ground_floor_investments_service_role_all" on public.ground_floor_investments;
create policy "ground_floor_investments_service_role_all"
on public.ground_floor_investments
for all
to service_role
using (true)
with check (true);

drop policy if exists "ground_floor_county_packages_service_role_all" on public.ground_floor_county_packages;
create policy "ground_floor_county_packages_service_role_all"
on public.ground_floor_county_packages
for all
to service_role
using (true)
with check (true);

drop policy if exists "ground_floor_investments_authenticated_read" on public.ground_floor_investments;
create policy "ground_floor_investments_authenticated_read"
on public.ground_floor_investments
for select
to authenticated
using (true);

drop policy if exists "ground_floor_county_packages_authenticated_read" on public.ground_floor_county_packages;
create policy "ground_floor_county_packages_authenticated_read"
on public.ground_floor_county_packages
for select
to authenticated
using (true);
