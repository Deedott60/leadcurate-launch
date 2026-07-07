create table if not exists public.orders (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid references public.customers(id) on delete set null,
  intake_request_id uuid references public.intake_requests(id) on delete set null,
  prospect_id uuid references public.prospects(id) on delete set null,
  customer_name text,
  customer_email text,
  market text not null,
  lane text not null,
  tier_key text,
  record_count integer,
  amount_cents integer,
  currency text not null default 'usd',
  status text not null default 'pending_payment',
  provider text,
  provider_reference text,
  payment_confirmed_at timestamptz,
  delivery_status text not null default 'not_started',
  delivery_triggered_at timestamptz,
  delivery_id uuid references public.deliveries(id) on delete set null,
  notes text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  order_id uuid references public.orders(id) on delete cascade,
  customer_id uuid references public.customers(id) on delete set null,
  provider text not null,
  provider_reference text,
  amount_cents integer,
  currency text not null default 'usd',
  status text not null default 'pending',
  payment_method text,
  test_mode boolean not null default false,
  confirmed_by text,
  confirmed_at timestamptz,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists orders_status_created_idx
  on public.orders (status, created_at desc);

create index if not exists orders_customer_email_idx
  on public.orders (lower(customer_email));

create index if not exists orders_intake_request_idx
  on public.orders (intake_request_id);

create index if not exists payments_order_idx
  on public.payments (order_id, created_at desc);

create unique index if not exists payments_provider_reference_uidx
  on public.payments (provider, provider_reference)
  where provider_reference is not null and provider_reference <> '';

alter table public.orders enable row level security;
alter table public.payments enable row level security;

revoke all on public.orders from anon, authenticated;
revoke all on public.payments from anon, authenticated;

grant all on public.orders to service_role;
grant all on public.payments to service_role;

comment on table public.orders is
  'LeadCurate payment readiness ledger. Stripe Payment Link and Derrick manual confirmation both create/update this record before manual_delivery_pipeline runs.';

comment on table public.payments is
  'Payment events tied to orders. Stores manual Cash App/Zelle confirmations and Stripe test/live references without choosing a provider in the schema.';
