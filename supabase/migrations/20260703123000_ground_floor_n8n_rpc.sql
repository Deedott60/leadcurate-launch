create extension if not exists pgcrypto;

insert into private.app_secrets (name, value)
values ('GROUND_FLOOR_N8N_API_KEY_SHA256', '525b0e475caa3c445e265037ca569f623f326b8da784441b3caf904d09edd69d')
on conflict (name) do update
set value = excluded.value,
    updated_at = now();

create or replace function public.ground_floor_check_n8n_token(auth_token text)
returns void
language plpgsql
security definer
set search_path = private, public, pg_temp
as $$
declare
  expected_hash text;
begin
  expected_hash := private.get_secret('GROUND_FLOOR_N8N_API_KEY_SHA256');
  if expected_hash is null
    or auth_token is null
    or encode(extensions.digest(convert_to(auth_token, 'UTF8'), 'sha256'), 'hex') <> expected_hash then
    raise exception 'invalid ground floor token' using errcode = '42501';
  end if;
end;
$$;

create or replace function public.upsert_ground_floor_investments(auth_token text, rows jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public, private, pg_temp
as $$
declare
  inserted_rows jsonb;
begin
  perform public.ground_floor_check_n8n_token(auth_token);

  with input_rows as (
    select *
    from jsonb_to_recordset(rows) as r(
      location text,
      state text,
      county text,
      company text,
      dollar_amount numeric,
      dollar_amount_text text,
      job_count integer,
      announcement_date date,
      project_stage text,
      source_url text,
      second_source_url text,
      confidence_level text,
      notes text
    )
  ),
  upserted as (
    insert into public.ground_floor_investments (
      location,
      state,
      county,
      company,
      dollar_amount,
      dollar_amount_text,
      job_count,
      announcement_date,
      project_stage,
      source_url,
      second_source_url,
      confidence_level,
      notes,
      updated_at
    )
    select
      location,
      state,
      county,
      company,
      dollar_amount,
      dollar_amount_text,
      job_count,
      announcement_date,
      project_stage,
      source_url,
      second_source_url,
      coalesce(confidence_level, 'medium'),
      notes,
      now()
    from input_rows
    on conflict (location, company, announcement_date, source_url)
    do update set
      state = excluded.state,
      county = excluded.county,
      dollar_amount = excluded.dollar_amount,
      dollar_amount_text = excluded.dollar_amount_text,
      job_count = excluded.job_count,
      project_stage = excluded.project_stage,
      second_source_url = excluded.second_source_url,
      confidence_level = excluded.confidence_level,
      notes = excluded.notes,
      updated_at = now()
    returning *
  )
  select coalesce(jsonb_agg(to_jsonb(upserted)), '[]'::jsonb)
  into inserted_rows
  from upserted;

  return jsonb_build_object(
    'ok', true,
    'count', jsonb_array_length(coalesce(rows, '[]'::jsonb)),
    'rows', inserted_rows
  );
end;
$$;

create or replace function public.insert_ground_floor_county_package(auth_token text, package jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public, private, pg_temp
as $$
declare
  package_id uuid;
  linked_investment_id uuid;
  source_file_values text[];
begin
  perform public.ground_floor_check_n8n_token(auth_token);

  select id
  into linked_investment_id
  from public.ground_floor_investments
  where location = package #>> '{investment_snapshot,location}'
    and company = package #>> '{investment_snapshot,company}'
    and announcement_date = nullif(package #>> '{investment_snapshot,announcement_date}', '')::date
  order by updated_at desc
  limit 1;

  select coalesce(array_agg(value), '{}'::text[])
  into source_file_values
  from jsonb_array_elements_text(coalesce(package -> 'source_files', '[]'::jsonb)) as value;

  insert into public.ground_floor_county_packages (
    market_slug,
    county,
    state,
    investment_id,
    investment_snapshot,
    property_snapshot,
    package_path,
    source_files,
    status
  )
  values (
    package ->> 'market_slug',
    package ->> 'county',
    package ->> 'state',
    linked_investment_id,
    coalesce(package -> 'investment_snapshot', '{}'::jsonb),
    coalesce(package -> 'property_snapshot', '{}'::jsonb),
    package ->> 'package_path',
    source_file_values,
    coalesce(package ->> 'status', 'ready_for_review')
  )
  returning id into package_id;

  return jsonb_build_object('ok', true, 'id', package_id);
end;
$$;

revoke all on function public.ground_floor_check_n8n_token(text) from public;
revoke all on function public.upsert_ground_floor_investments(text, jsonb) from public;
revoke all on function public.insert_ground_floor_county_package(text, jsonb) from public;

grant execute on function public.upsert_ground_floor_investments(text, jsonb) to anon, authenticated, service_role;
grant execute on function public.insert_ground_floor_county_package(text, jsonb) to anon, authenticated, service_role;
