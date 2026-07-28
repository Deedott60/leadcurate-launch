create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  client_name text not null,
  client_entity text,
  client_email text,
  status text not null default 'planning',
  commercial_basis text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by text not null default 'system'
);

create table if not exists public.project_markets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  market text not null,
  categories text[],
  status text not null default 'planning',
  source_date date,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by text not null default 'system'
);

create unique index if not exists project_markets_project_market_key
  on public.project_markets (project_id, lower(market));

create table if not exists public.project_items (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  kind text not null check (kind in ('task', 'decision', 'blocker', 'deliverable')),
  title text not null,
  detail text,
  owner text not null default 'derrick'
    check (owner in ('derrick', 'claude', 'codex', 'hermes')),
  status text not null default 'open',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by text not null default 'system'
);

create index if not exists project_items_project_status_idx
  on public.project_items (project_id, status, updated_at desc);

create table if not exists public.project_assets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  kind text not null check (
    kind in ('landing_page', 'domain', 'logo', 'config', 'tool_instance', 'document', 'other')
  ),
  label text not null,
  url text,
  status text not null default 'waiting',
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by text not null default 'system'
);

create index if not exists project_assets_project_kind_idx
  on public.project_assets (project_id, kind, updated_at desc);

alter table public.activity_feed
  add column if not exists project_id uuid references public.projects(id) on delete set null;

create index if not exists activity_feed_project_created_idx
  on public.activity_feed (project_id, created_at desc);

create or replace function public.set_project_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

revoke all on function public.set_project_updated_at() from public;

drop trigger if exists projects_set_updated_at on public.projects;
create trigger projects_set_updated_at
before update on public.projects
for each row execute function public.set_project_updated_at();

drop trigger if exists project_markets_set_updated_at on public.project_markets;
create trigger project_markets_set_updated_at
before update on public.project_markets
for each row execute function public.set_project_updated_at();

drop trigger if exists project_items_set_updated_at on public.project_items;
create trigger project_items_set_updated_at
before update on public.project_items
for each row execute function public.set_project_updated_at();

drop trigger if exists project_assets_set_updated_at on public.project_assets;
create trigger project_assets_set_updated_at
before update on public.project_assets
for each row execute function public.set_project_updated_at();

alter table public.projects enable row level security;
alter table public.project_markets enable row level security;
alter table public.project_items enable row level security;
alter table public.project_assets enable row level security;

grant select, insert, update on public.projects to anon, authenticated;
grant select, insert, update, delete on public.project_markets to anon, authenticated;
grant select, insert, update, delete on public.project_items to anon, authenticated;
grant select, insert, update, delete on public.project_assets to anon, authenticated;

drop policy if exists "anon select projects" on public.projects;
create policy "anon select projects" on public.projects
for select to anon using (true);

drop policy if exists "anon insert projects scoped" on public.projects;
create policy "anon insert projects scoped" on public.projects
for insert to anon with check (
  length(trim(name)) > 0
  and length(trim(client_name)) > 0
  and length(trim(slug)) > 0
);

drop policy if exists "anon update projects scoped" on public.projects;
create policy "anon update projects scoped" on public.projects
for update to anon
using (
  length(trim(name)) > 0
  and length(trim(client_name)) > 0
  and length(trim(slug)) > 0
)
with check (
  length(trim(name)) > 0
  and length(trim(client_name)) > 0
  and length(trim(slug)) > 0
);

drop policy if exists "auth manage projects" on public.projects;
create policy "auth manage projects" on public.projects
for all to authenticated
using ((select auth.uid()) is not null)
with check ((select auth.uid()) is not null);

drop policy if exists "anon select project markets" on public.project_markets;
create policy "anon select project markets" on public.project_markets
for select to anon using (true);

drop policy if exists "anon insert project markets scoped" on public.project_markets;
create policy "anon insert project markets scoped" on public.project_markets
for insert to anon with check (length(trim(market)) > 0);

drop policy if exists "anon update project markets scoped" on public.project_markets;
create policy "anon update project markets scoped" on public.project_markets
for update to anon
using (length(trim(market)) > 0)
with check (length(trim(market)) > 0);

drop policy if exists "anon delete project markets" on public.project_markets;
create policy "anon delete project markets" on public.project_markets
for delete to anon using (length(trim(market)) > 0);

drop policy if exists "auth manage project markets" on public.project_markets;
create policy "auth manage project markets" on public.project_markets
for all to authenticated
using ((select auth.uid()) is not null)
with check ((select auth.uid()) is not null);

drop policy if exists "anon select project items" on public.project_items;
create policy "anon select project items" on public.project_items
for select to anon using (true);

drop policy if exists "anon insert project items scoped" on public.project_items;
create policy "anon insert project items scoped" on public.project_items
for insert to anon with check (
  kind in ('task', 'decision', 'blocker', 'deliverable')
  and owner in ('derrick', 'claude', 'codex', 'hermes')
  and length(trim(title)) > 0
);

drop policy if exists "anon update project items scoped" on public.project_items;
create policy "anon update project items scoped" on public.project_items
for update to anon using (
  kind in ('task', 'decision', 'blocker', 'deliverable')
  and owner in ('derrick', 'claude', 'codex', 'hermes')
  and length(trim(title)) > 0
) with check (
  kind in ('task', 'decision', 'blocker', 'deliverable')
  and owner in ('derrick', 'claude', 'codex', 'hermes')
  and length(trim(title)) > 0
);

drop policy if exists "anon delete project items" on public.project_items;
create policy "anon delete project items" on public.project_items
for delete to anon using (
  kind in ('task', 'decision', 'blocker', 'deliverable')
  and owner in ('derrick', 'claude', 'codex', 'hermes')
  and length(trim(title)) > 0
);

drop policy if exists "auth manage project items" on public.project_items;
create policy "auth manage project items" on public.project_items
for all to authenticated
using ((select auth.uid()) is not null)
with check ((select auth.uid()) is not null);

drop policy if exists "anon select project assets" on public.project_assets;
create policy "anon select project assets" on public.project_assets
for select to anon using (true);

drop policy if exists "anon insert project assets scoped" on public.project_assets;
create policy "anon insert project assets scoped" on public.project_assets
for insert to anon with check (
  kind in ('landing_page', 'domain', 'logo', 'config', 'tool_instance', 'document', 'other')
  and length(trim(label)) > 0
);

drop policy if exists "anon update project assets scoped" on public.project_assets;
create policy "anon update project assets scoped" on public.project_assets
for update to anon using (
  kind in ('landing_page', 'domain', 'logo', 'config', 'tool_instance', 'document', 'other')
  and length(trim(label)) > 0
) with check (
  kind in ('landing_page', 'domain', 'logo', 'config', 'tool_instance', 'document', 'other')
  and length(trim(label)) > 0
);

drop policy if exists "anon delete project assets" on public.project_assets;
create policy "anon delete project assets" on public.project_assets
for delete to anon using (
  kind in ('landing_page', 'domain', 'logo', 'config', 'tool_instance', 'document', 'other')
  and length(trim(label)) > 0
);

drop policy if exists "auth manage project assets" on public.project_assets;
create policy "auth manage project assets" on public.project_assets
for all to authenticated
using ((select auth.uid()) is not null)
with check ((select auth.uid()) is not null);

do $$
declare
  table_name text;
begin
  foreach table_name in array array['projects', 'project_markets', 'project_items', 'project_assets']
  loop
    if not exists (
      select 1
      from pg_publication_tables
      where pubname = 'supabase_realtime'
        and schemaname = 'public'
        and tablename = table_name
    ) then
      execute format('alter publication supabase_realtime add table public.%I', table_name);
    end if;
  end loop;
end;
$$;

with reggie as (
  insert into public.projects (
    slug,
    name,
    client_name,
    client_entity,
    client_email,
    status,
    commercial_basis,
    notes,
    updated_by
  )
  values (
    'reggie-adams',
    'Reggie Adams project',
    'Reggie Adams',
    'The 3 CCC''S Consulting Firm LLC',
    'mrreggieadams@gmail.com',
    'planning',
    null,
    'Current project workspace. Markets, categories, pricing, and terms have not been agreed.',
    'claude-code'
  )
  on conflict (slug) do update set
    name = excluded.name,
    client_name = excluded.client_name,
    client_entity = excluded.client_entity,
    client_email = excluded.client_email,
    status = excluded.status,
    commercial_basis = excluded.commercial_basis,
    notes = excluded.notes,
    updated_by = excluded.updated_by
  returning id
)
insert into public.project_items (project_id, kind, title, detail, owner, status, updated_by)
select reggie.id, seed.kind, seed.title, seed.detail, seed.owner, seed.status, 'claude-code'
from reggie
cross join (
  values
    (
      'decision',
      'Agree on a new project scope',
      'There is no current price or agreed commercial scope. The earlier invoice is historical only and the order row must not be changed without Derrick''s instruction.',
      'derrick',
      'open'
    ),
    (
      'decision',
      'Confirm the markets and data categories Reggie wants',
      'No market or category is currently approved for this project. Add markets here only after Derrick confirms them with Reggie.',
      'derrick',
      'open'
    ),
    (
      'blocker',
      'Collect Reggie''s public business name and brand assets',
      'Needed: public business name, logo, colors, phone, mailing address, domain decision, and lead-routing inbox.',
      'derrick',
      'open'
    ),
    (
      'deliverable',
      'White-label website demo',
      'The reusable multi-page website is live at premier-demo.leadcurate.com. Reggie''s branding is not active.',
      'claude',
      'complete'
    ),
    (
      'deliverable',
      'Property Decision Tool demo',
      'The reusable tool is live with sample data. Real market data and private customer access are not connected.',
      'claude',
      'complete'
    ),
    (
      'deliverable',
      'Inactive Reggie client configuration',
      'Prepared in the separate whitelabel-investor-site repository. It is deliberately inactive and not deployed.',
      'codex',
      'complete'
    )
) as seed(kind, title, detail, owner, status)
where not exists (
  select 1
  from public.project_items existing
  where existing.project_id = reggie.id
    and existing.title = seed.title
);

with reggie as (
  select id from public.projects where slug = 'reggie-adams'
)
insert into public.project_assets (project_id, kind, label, url, status, notes, updated_by)
select reggie.id, seed.kind, seed.label, seed.url, seed.status, seed.notes, 'claude-code'
from reggie
cross join (
  values
    (
      'landing_page',
      'Reggie landing page',
      null,
      'waiting',
      'Waiting for the public business name, approved terms, domain, and brand assets.'
    ),
    (
      'tool_instance',
      'Property Decision Tool demo',
      'https://premier-demo.leadcurate.com/tool',
      'demo',
      'Sample data only. Reggie-specific access is not active.'
    ),
    (
      'config',
      'Prepared Reggie client configuration',
      'https://github.com/Deedott60/whitelabel-investor-site/tree/codex/reggie-c1-prep/config/clients',
      'prepared',
      'Inactive configuration on a separate repository branch. Not imported or deployed.'
    )
) as seed(kind, label, url, status, notes)
where not exists (
  select 1
  from public.project_assets existing
  where existing.project_id = reggie.id
    and existing.kind = seed.kind
    and existing.label = seed.label
);
