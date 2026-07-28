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

drop policy if exists "anon update project markets scoped" on public.project_markets;
create policy "anon update project markets scoped" on public.project_markets
for update to anon
using (length(trim(market)) > 0)
with check (length(trim(market)) > 0);

drop policy if exists "anon delete project markets" on public.project_markets;
create policy "anon delete project markets" on public.project_markets
for delete to anon using (length(trim(market)) > 0);

drop policy if exists "anon update project items scoped" on public.project_items;
create policy "anon update project items scoped" on public.project_items
for update to anon
using (
  kind in ('task', 'decision', 'blocker', 'deliverable')
  and owner in ('derrick', 'claude', 'codex', 'hermes')
  and length(trim(title)) > 0
)
with check (
  kind in ('task', 'decision', 'blocker', 'deliverable')
  and owner in ('derrick', 'claude', 'codex', 'hermes')
  and length(trim(title)) > 0
);

drop policy if exists "anon delete project items" on public.project_items;
create policy "anon delete project items" on public.project_items
for delete to anon
using (
  kind in ('task', 'decision', 'blocker', 'deliverable')
  and owner in ('derrick', 'claude', 'codex', 'hermes')
  and length(trim(title)) > 0
);

drop policy if exists "anon update project assets scoped" on public.project_assets;
create policy "anon update project assets scoped" on public.project_assets
for update to anon
using (
  kind in ('landing_page', 'domain', 'logo', 'config', 'tool_instance', 'document', 'other')
  and length(trim(label)) > 0
)
with check (
  kind in ('landing_page', 'domain', 'logo', 'config', 'tool_instance', 'document', 'other')
  and length(trim(label)) > 0
);

drop policy if exists "anon delete project assets" on public.project_assets;
create policy "anon delete project assets" on public.project_assets
for delete to anon
using (
  kind in ('landing_page', 'domain', 'logo', 'config', 'tool_instance', 'document', 'other')
  and length(trim(label)) > 0
);
