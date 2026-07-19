create table if not exists public.dollar_fulfillment_jobs (
  id uuid primary key default gen_random_uuid(),
  order_code text not null unique,
  intake_request_id uuid not null references public.intake_requests(id),
  customer_name text not null,
  customer_email text not null,
  market text not null,
  market_display text not null,
  lane text not null,
  lane_display text not null,
  pack_label text not null,
  pack_size integer not null check (pack_size in (20, 50, 250, 500, 1000)),
  cycle text not null,
  cycle_slug text not null,
  status text not null default 'queued' check (status in ('queued', 'processing', 'delivered', 'failed')),
  batch_no integer,
  delivery_dir text,
  error text,
  attempt_count integer not null default 0,
  claimed_at timestamptz,
  delivered_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.dollar_fulfillment_jobs enable row level security;

create or replace function public.claim_dollar_fulfillment_job()
returns public.dollar_fulfillment_jobs
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  picked public.dollar_fulfillment_jobs;
begin
  select * into picked
  from public.dollar_fulfillment_jobs
  where status = 'queued'
     or (status = 'processing' and claimed_at < now() - interval '15 minutes')
  order by created_at
  for update skip locked
  limit 1;

  if not found then return null; end if;

  update public.dollar_fulfillment_jobs
  set status = 'processing', claimed_at = now(), attempt_count = attempt_count + 1,
      error = null, updated_at = now()
  where id = picked.id
  returning * into picked;
  return picked;
end;
$$;

create or replace function public.reserve_dollar_batch(
  p_market text,
  p_lane text,
  p_batch_no integer,
  p_cycle text
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  picked public.dollar_batches;
begin
  select * into picked
  from public.dollar_batches
  where market = p_market and lane = p_lane and batch_no = p_batch_no
    and cycle = p_cycle and status = 'live'
  for update;

  if not found then raise exception 'Live Dollar Leads batch not found'; end if;
  if picked.seats_sold >= picked.seats_total then raise exception 'Dollar Leads batch is sold out'; end if;

  update public.dollar_batches
  set seats_sold = seats_sold + 1
  where id = picked.id
  returning * into picked;
  return to_jsonb(picked);
end;
$$;

revoke all on table public.dollar_fulfillment_jobs from anon, authenticated;
revoke all on function public.claim_dollar_fulfillment_job() from public, anon, authenticated;
revoke all on function public.reserve_dollar_batch(text, text, integer, text) from public, anon, authenticated;
grant all on table public.dollar_fulfillment_jobs to service_role;
grant execute on function public.claim_dollar_fulfillment_job() to service_role;
grant execute on function public.reserve_dollar_batch(text, text, integer, text) to service_role;
