create or replace function public.get_dollar_inventory_summary()
returns table (
  market text,
  market_display text,
  lane text,
  lane_display text,
  cycle text,
  open_seats bigint,
  can_20 boolean,
  can_50 boolean,
  can_250 boolean,
  can_500 boolean,
  can_1000 boolean
)
language sql
stable
security invoker
set search_path = public
as $$
  select
    b.market,
    max(b.market_display) as market_display,
    b.lane,
    max(b.lane_display) as lane_display,
    max(b.cycle) as cycle,
    sum(greatest(b.seats_total - b.seats_sold, 0))::bigint as open_seats,
    bool_or(b.size >= 20 and b.seats_sold < b.seats_total) as can_20,
    bool_or(b.size >= 50 and b.seats_sold < b.seats_total) as can_50,
    bool_or(b.size >= 250 and b.seats_sold < b.seats_total) as can_250,
    bool_or(b.size >= 500 and b.seats_sold < b.seats_total) as can_500,
    exists (
      select 1
      from public.dollar_batches first_batch
      join public.dollar_batches second_batch
        on second_batch.market = first_batch.market
       and second_batch.lane = first_batch.lane
       and second_batch.cycle = first_batch.cycle
       and second_batch.batch_no = first_batch.batch_no + 1
      where first_batch.market = b.market
        and first_batch.lane = b.lane
        and first_batch.status = 'live'
        and second_batch.status = 'live'
        and first_batch.size >= 500
        and second_batch.size >= 500
        and first_batch.seats_sold = 0
        and second_batch.seats_sold = 0
    ) as can_1000
  from public.dollar_batches b
  where b.status = 'live'
  group by b.market, b.lane;
$$;

revoke all on function public.get_dollar_inventory_summary() from public;
grant execute on function public.get_dollar_inventory_summary() to anon, authenticated, service_role;

comment on function public.get_dollar_inventory_summary() is
  'Public-safe aggregate Dollar Leads availability; exposes no parcel or customer data.';
