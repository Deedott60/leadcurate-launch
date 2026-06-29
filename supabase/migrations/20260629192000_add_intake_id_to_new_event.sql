create or replace function public.auto_pipeline_from_intake()
returns trigger
language plpgsql
set search_path to 'public', 'pg_temp'
as $function$
declare
  market_str text;
  list_str text;
begin
  select array_to_string(new.markets, ', ') into market_str;
  select array_to_string(new.list_type, ', ') into list_str;

  insert into public.prospects (intake_request_id, name, contact, channel, source, status, notes)
  values (
    new.id,
    coalesce(new.name, '(no name)'),
    coalesce(new.email, new.phone, ''),
    case when new.phone is not null and new.phone != '' then 'sms' else 'email' end,
    'intake-form',
    'replied',
    concat(
      'Markets: ', coalesce(market_str, 'not specified'),
      E'\nList type: ', coalesce(list_str, 'not specified'),
      E'\nUrgency: ', coalesce(new.urgency, '-'),
      E'\nVolume: ', coalesce(new.volume, '-'),
      E'\nRole: ', coalesce(new.role, '-'),
      E'\nNotes: ', coalesce(new.notes, '')
    )
  );

  insert into public.activity_feed (event_type, source, title, body, target)
  values (
    'intake:new',
    'intake-form',
    concat('New intake: ', coalesce(new.name, 'unknown'), ' - ', coalesce(market_str, 'no market')),
    concat(
      'Intake ID: ', new.id,
      E'\nEmail: ', coalesce(new.email, '-'),
      E'\nPhone: ', coalesce(new.phone, '-'),
      E'\nMarkets: ', coalesce(market_str, '-'),
      E'\nList type: ', coalesce(list_str, '-'),
      E'\nUrgency: ', coalesce(new.urgency, '-'),
      E'\nVolume: ', coalesce(new.volume, '-'),
      E'\nRole: ', coalesce(new.role, '-'),
      E'\nNotes: ', coalesce(new.notes, '-')
    ),
    'derrick'
  );

  return new;
end;
$function$;
