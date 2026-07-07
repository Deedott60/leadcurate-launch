declare const Deno: {
  env: { get(name: string): string | undefined };
  serve(handler: (req: Request) => Response | Promise<Response>): void;
};

const SB_URL = Deno.env.get("SUPABASE_URL") ?? "https://jdmlsraqioigbukspduo.supabase.co";
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const ADMIN_TOKEN = Deno.env.get("LEADCURATE_PAYMENT_ADMIN_TOKEN") ?? Deno.env.get("HOSTINGER_WEBHOOK_SECRET") ?? "";

const headers = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, content-type, x-leadcurate-payment-token",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

type Payload = {
  mode?: "manual_confirm" | "stripe_payment_link";
  order_id?: string;
  customer_id?: string;
  intake_request_id?: string;
  prospect_id?: string;
  customer_name?: string;
  customer_email?: string;
  market?: string;
  lane?: string;
  tier_key?: string;
  record_count?: number;
  amount_cents?: number;
  currency?: string;
  provider?: string;
  provider_reference?: string;
  payment_method?: string;
  test_mode?: boolean;
  confirmed_by?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers });
}

function adminAuthorized(req: Request) {
  if (!ADMIN_TOKEN) return false;
  const bearer = req.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  const explicit = req.headers.get("x-leadcurate-payment-token");
  return bearer === ADMIN_TOKEN || explicit === ADMIN_TOKEN;
}

function serviceHeaders(extra: Record<string, string> = {}) {
  if (!SERVICE_KEY) throw new Error("SUPABASE_SERVICE_ROLE_KEY is not configured");
  return {
    apikey: SERVICE_KEY,
    Authorization: `Bearer ${SERVICE_KEY}`,
    "Content-Type": "application/json",
    ...extra,
  };
}

function cleanString(value: unknown) {
  const text = String(value ?? "").trim();
  return text || null;
}

function required(value: unknown, name: string) {
  const text = cleanString(value);
  if (!text) throw new Error(`${name} is required`);
  return text;
}

async function supabase(path: string, init: RequestInit) {
  const res = await fetch(`${SB_URL}/rest/v1/${path}`, init);
  const text = await res.text();
  if (!res.ok) throw new Error(`Supabase ${res.status} ${path}: ${text}`);
  return text ? JSON.parse(text) : null;
}

async function activity(event_type: string, title: string, body: string, target = "derrick") {
  await supabase("activity_feed", {
    method: "POST",
    headers: serviceHeaders({ Prefer: "return=minimal" }),
    body: JSON.stringify({ event_type, source: "payment-confirmation", title, body, target }),
  }).catch(() => {});
}

async function upsertCustomer(p: Payload) {
  const email = cleanString(p.customer_email);
  if (!email) return null;
  const existing = await supabase(`customers?email=eq.${encodeURIComponent(email)}&select=id&limit=1`, {
    method: "GET",
    headers: serviceHeaders(),
  });
  if (existing?.[0]?.id) return existing[0].id as string;
  const inserted = await supabase("customers?select=id", {
    method: "POST",
    headers: serviceHeaders({ Prefer: "return=representation" }),
    body: JSON.stringify({
      name: cleanString(p.customer_name),
      email,
      status: "customer",
    }),
  });
  return inserted?.[0]?.id ?? null;
}

async function upsertOrder(p: Payload, customerId: string | null) {
  if (p.order_id) {
    const updated = await supabase(`orders?id=eq.${encodeURIComponent(p.order_id)}&select=*`, {
      method: "PATCH",
      headers: serviceHeaders({ Prefer: "return=representation" }),
      body: JSON.stringify({
        customer_id: customerId ?? p.customer_id ?? undefined,
        status: "paid",
        provider: cleanString(p.provider),
        provider_reference: cleanString(p.provider_reference),
        payment_confirmed_at: new Date().toISOString(),
        delivery_status: "ready_for_manual_pipeline",
        notes: cleanString(p.notes),
        metadata: p.metadata ?? {},
        updated_at: new Date().toISOString(),
      }),
    });
    if (!updated?.[0]) throw new Error("order_id not found");
    return updated[0];
  }

  const inserted = await supabase("orders?select=*", {
    method: "POST",
    headers: serviceHeaders({ Prefer: "return=representation" }),
    body: JSON.stringify({
      customer_id: customerId ?? p.customer_id ?? null,
      intake_request_id: cleanString(p.intake_request_id),
      prospect_id: cleanString(p.prospect_id),
      customer_name: cleanString(p.customer_name),
      customer_email: cleanString(p.customer_email),
      market: required(p.market, "market"),
      lane: required(p.lane, "lane"),
      tier_key: cleanString(p.tier_key),
      record_count: Number.isFinite(Number(p.record_count)) ? Number(p.record_count) : null,
      amount_cents: Number.isFinite(Number(p.amount_cents)) ? Number(p.amount_cents) : null,
      currency: cleanString(p.currency) ?? "usd",
      status: "paid",
      provider: cleanString(p.provider),
      provider_reference: cleanString(p.provider_reference),
      payment_confirmed_at: new Date().toISOString(),
      delivery_status: "ready_for_manual_pipeline",
      notes: cleanString(p.notes),
      metadata: p.metadata ?? {},
    }),
  });
  return inserted?.[0];
}

async function insertPayment(p: Payload, order: Record<string, unknown>, customerId: string | null) {
  const provider = cleanString(p.provider) ?? (p.mode === "stripe_payment_link" ? "stripe" : "manual");
  const payment = await supabase("payments?select=*", {
    method: "POST",
    headers: serviceHeaders({ Prefer: "return=representation,resolution=ignore-duplicates" }),
    body: JSON.stringify({
      order_id: order.id,
      customer_id: customerId,
      provider,
      provider_reference: cleanString(p.provider_reference),
      amount_cents: Number.isFinite(Number(p.amount_cents)) ? Number(p.amount_cents) : order.amount_cents ?? null,
      currency: cleanString(p.currency) ?? String(order.currency ?? "usd"),
      status: "paid",
      payment_method: cleanString(p.payment_method) ?? provider,
      test_mode: Boolean(p.test_mode),
      confirmed_by: cleanString(p.confirmed_by) ?? "derrick",
      confirmed_at: new Date().toISOString(),
      raw_payload: p,
    }),
  });
  return payment?.[0] ?? null;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers });
  if (req.method !== "POST") return json({ ok: false, error: "POST required" }, 405);
  if (!adminAuthorized(req)) return json({ ok: false, error: "payment admin token required" }, 401);

  try {
    const p = await req.json() as Payload;
    const mode = p.mode ?? "manual_confirm";
    if (!["manual_confirm", "stripe_payment_link"].includes(mode)) {
      return json({ ok: false, error: `unknown mode ${mode}` }, 400);
    }

    const customerId = p.customer_id ?? await upsertCustomer(p);
    const provider = cleanString(p.provider) ?? (mode === "stripe_payment_link" ? "stripe" : "manual");
    const order = await upsertOrder({ ...p, mode, provider }, customerId);
    const payment = await insertPayment({ ...p, mode, provider }, order, customerId);

    await activity(
      "conf:status",
      `Payment confirmed: ${order.market}/${order.lane}`,
      JSON.stringify({
        order_id: order.id,
        payment_id: payment?.id ?? null,
        customer: order.customer_email ?? order.customer_name,
        provider,
        amount_cents: order.amount_cents,
        delivery_status: order.delivery_status,
        trigger_point: "manual_delivery_pipeline can now be run manually for this order",
      }, null, 2),
    );

    return json({ ok: true, mode, order, payment, trigger_point: "manual_delivery_pipeline" });
  } catch (err) {
    await activity("conf:blocker", "Payment confirmation failed", String((err as Error)?.message ?? err));
    return json({ ok: false, error: String((err as Error)?.message ?? err) }, 500);
  }
});
