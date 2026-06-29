alter table public.intake_requests
  add column if not exists recommended_tier text,
  add column if not exists recommendation_note text,
  add column if not exists routed_at timestamptz;

alter table public.prospects
  add column if not exists intake_request_id uuid references public.intake_requests(id) on delete set null,
  add column if not exists recommended_tier text,
  add column if not exists recommendation_note text;

create index if not exists prospects_intake_request_id_idx
  on public.prospects (intake_request_id);

create index if not exists intake_requests_routed_idx
  on public.intake_requests (routed_at, created_at desc);

create index if not exists activity_feed_event_type_idx
  on public.activity_feed (event_type, created_at desc);

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
    'conf:status',
    'system',
    concat('New intake from ', coalesce(new.name, 'unknown'), ' - auto-added to Pipeline'),
    concat(
      'Name: ', coalesce(new.name, '-'),
      E'\nEmail: ', coalesce(new.email, '-'),
      E'\nPhone: ', coalesce(new.phone, '-'),
      E'\nMarkets: ', coalesce(market_str, '-'),
      E'\nList type: ', coalesce(list_str, '-'),
      E'\nUrgency: ', coalesce(new.urgency, '-'),
      E'\nStage set to: Replied (they filled out the form)'
    ),
    'claude'
  );

  return new;
end;
$function$;

create or replace function public.route_intake_recommendation(
  intake_id uuid,
  recommended_tier text,
  recommendation_note text
)
returns jsonb
language plpgsql
security definer
set search_path = public, private, pg_temp
as $function$
declare
  request_headers jsonb;
  router_secret text;
  expected_secret text;
  intake_row public.intake_requests%rowtype;
  updated_prospect_id uuid;
begin
  request_headers := coalesce(nullif(current_setting('request.headers', true), ''), '{}')::jsonb;
  router_secret := request_headers ->> 'x-leadcurate-router-secret';
  expected_secret := private.get_secret('HOSTINGER_WEBHOOK_SECRET');

  if expected_secret is null or router_secret is null or router_secret <> expected_secret then
    raise exception 'invalid router secret' using errcode = '42501';
  end if;

  select * into intake_row
  from public.intake_requests
  where id = route_intake_recommendation.intake_id;

  if not found then
    raise exception 'intake not found' using errcode = 'P0002';
  end if;

  update public.intake_requests
  set recommended_tier = route_intake_recommendation.recommended_tier,
      recommendation_note = route_intake_recommendation.recommendation_note,
      routed_at = now()
  where id = route_intake_recommendation.intake_id;

  update public.prospects
  set intake_request_id = route_intake_recommendation.intake_id,
      recommended_tier = route_intake_recommendation.recommended_tier,
      recommendation_note = route_intake_recommendation.recommendation_note,
      notes = concat_ws(
        E'\n\n',
        notes,
        concat(
          'Recommended tier: ', route_intake_recommendation.recommended_tier,
          E'\nOperator note: ', route_intake_recommendation.recommendation_note
        )
      ),
      updated_at = now()
  where id = coalesce(
    (
      select p.id
      from public.prospects p
      where p.intake_request_id = route_intake_recommendation.intake_id
      order by p.created_at desc
      limit 1
    ),
    (
      select p.id
      from public.prospects p
      where p.source = 'intake-form'
        and p.contact = coalesce(intake_row.email, intake_row.phone, '')
        and p.created_at >= intake_row.created_at - interval '5 minutes'
      order by p.created_at desc
      limit 1
    )
  )
  returning id into updated_prospect_id;

  insert into public.activity_feed (event_type, source, title, body, target)
  values (
    'intake:triaged',
    'n8n',
    concat(
      'Intake triaged: ',
      coalesce(intake_row.name, intake_row.email, intake_row.phone, 'unknown'),
      ' -> ',
      route_intake_recommendation.recommended_tier
    ),
    route_intake_recommendation.recommendation_note,
    'derrick'
  );

  return jsonb_build_object(
    'ok', true,
    'intake_id', route_intake_recommendation.intake_id,
    'prospect_id', updated_prospect_id,
    'recommended_tier', route_intake_recommendation.recommended_tier
  );
end;
$function$;

revoke all on function public.route_intake_recommendation(uuid, text, text) from public;
grant execute on function public.route_intake_recommendation(uuid, text, text) to anon;
