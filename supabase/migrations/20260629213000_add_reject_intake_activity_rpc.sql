create or replace function public.reject_intake_activity(activity_id uuid)
returns public.activity_feed
language plpgsql
security definer
set search_path = public
as $$
declare
  updated public.activity_feed;
begin
  update public.activity_feed
  set
    event_type = 'intake:rejected',
    read = true
  where id = activity_id
    and event_type = 'intake:new'
    and target = 'derrick'
    and source like 'intake-form%'
  returning * into updated;

  return updated;
end;
$$;

revoke all on function public.reject_intake_activity(uuid) from public;
grant execute on function public.reject_intake_activity(uuid) to anon, authenticated;
