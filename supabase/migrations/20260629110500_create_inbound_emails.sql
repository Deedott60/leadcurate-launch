create table if not exists public.inbound_emails (
  id uuid primary key default gen_random_uuid(),
  received_at timestamptz not null default now(),
  from_addr text not null,
  subject text,
  preview text,
  raw_payload jsonb not null,
  handled boolean default false
);

alter table public.inbound_emails enable row level security;

create policy "auth read inbound_emails"
  on public.inbound_emails
  for select
  to authenticated
  using ((select auth.uid()) is not null);

create policy "auth update inbound_emails"
  on public.inbound_emails
  for update
  to authenticated
  using ((select auth.uid()) is not null)
  with check ((select auth.uid()) is not null);
