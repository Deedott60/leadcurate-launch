create or replace function public.reserve_dollar_founders_batches(
  p_market text,
  p_lane text,
  p_start_batch_no integer,
  p_cycle text
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_ids uuid[];
  v_batches jsonb;
  v_slots_sold integer;
begin
  perform 1
  from public.dollar_promos
  where name = 'founders-20'
    and status = 'live'
    and slots_sold < slots_total
  for update;

  if not found then
    raise exception 'Founders Deal is sold out or inactive';
  end if;

  select array_agg(candidate.id order by candidate.batch_no)
  into v_ids
  from (
    select id, batch_no
    from public.dollar_batches
    where market = p_market
      and lane = p_lane
      and cycle = p_cycle
      and batch_no in (p_start_batch_no, p_start_batch_no + 1)
      and status = 'live'
      and seats_sold = 0
    for update
  ) as candidate;

  if coalesce(cardinality(v_ids), 0) <> 2 then
    raise exception 'Founders Deal requires two consecutive, completely unsold live batches';
  end if;

  update public.dollar_batches
  set seats_sold = seats_total,
      status = 'retired'
  where id = any(v_ids);

  update public.dollar_promos
  set slots_sold = slots_sold + 1
  where name = 'founders-20'
  returning slots_sold into v_slots_sold;

  select jsonb_agg(to_jsonb(batch_row) order by batch_row.batch_no)
  into v_batches
  from public.dollar_batches as batch_row
  where batch_row.id = any(v_ids);

  return jsonb_build_object(
    'batches', v_batches,
    'promo_slots_sold', v_slots_sold
  );
end;
$$;

revoke all on function public.reserve_dollar_founders_batches(text, text, integer, text) from public;
revoke all on function public.reserve_dollar_founders_batches(text, text, integer, text) from anon;
revoke all on function public.reserve_dollar_founders_batches(text, text, integer, text) from authenticated;
grant execute on function public.reserve_dollar_founders_batches(text, text, integer, text) to service_role;
