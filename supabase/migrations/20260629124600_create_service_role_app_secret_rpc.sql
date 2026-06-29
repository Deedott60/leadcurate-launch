grant usage on schema private to service_role;

create or replace function public.get_app_secret(secret_name text)
returns text
language sql
security definer
set search_path = private, public, pg_temp
as $$
  select private.get_secret(secret_name);
$$;

revoke all on function public.get_app_secret(text) from public;
revoke all on function public.get_app_secret(text) from anon;
revoke all on function public.get_app_secret(text) from authenticated;
grant execute on function public.get_app_secret(text) to service_role;
