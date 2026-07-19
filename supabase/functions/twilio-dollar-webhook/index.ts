const SB_URL = Deno.env.get("SUPABASE_URL") ?? "https://jdmlsraqioigbukspduo.supabase.co";

function adminKey() {
  const direct = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (direct) return direct;
  try { return JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}").default ?? ""; } catch { return ""; }
}

async function secret(name: string) {
  const key = adminKey();
  const res = await fetch(`${SB_URL}/rest/v1/rpc/get_app_secret`, { method: "POST", headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json" }, body: JSON.stringify({ secret_name: name }) });
  return res.ok ? await res.json() : "";
}

async function rest(path: string, init: RequestInit = {}) {
  const key = adminKey();
  const res = await fetch(`${SB_URL}/rest/v1/${path}`, { ...init, headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json", ...(init.headers ?? {}) } });
  const text = await res.text();
  if (!res.ok) throw new Error(`Supabase ${res.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

function xml(message: string, status = 200) {
  const safe = message.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><Response><Message>${safe}</Message></Response>`, { status, headers: { "Content-Type": "text/xml" } });
}

function normalizePhone(value: string) { return value.replace(/[^+\d]/g, ""); }

async function validTwilioSignature(url: string, form: URLSearchParams, signature: string, token: string) {
  let source = url;
  for (const key of [...new Set([...form.keys()])].sort()) {
    for (const value of form.getAll(key).sort()) source += key + value;
  }
  const cryptoKey = await crypto.subtle.importKey("raw", new TextEncoder().encode(token), { name: "HMAC", hash: "SHA-1" }, false, ["sign"]);
  const signed = new Uint8Array(await crypto.subtle.sign("HMAC", cryptoKey, new TextEncoder().encode(source)));
  const expected = btoa(String.fromCharCode(...signed));
  return signature.length === expected.length && signature.split("").every((c, i) => c === expected[i]);
}

const PACK_SIZES: Record<string, number> = {
  "Starter $5 (50 records)": 50,
  "Work $15 (250 records)": 250,
  "Full $25 (500 records)": 500,
  "Fresh Scrub $20 (20 records)": 20,
  "Founders Deal $50 (1,000 records)": 1000,
};

function cycleSlug(cycle: string) {
  const parsed = new Date(`1 ${cycle} UTC`);
  if (Number.isNaN(parsed.getTime())) throw new Error(`Cannot parse cycle ${cycle}`);
  return `${parsed.getUTCFullYear()}-${String(parsed.getUTCMonth() + 1).padStart(2, "0")}`;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return xml("POST required", 405);
  try {
    const [authToken, authorizedPhone] = await Promise.all([secret("TWILIO_AUTH_TOKEN"), secret("DOLLAR_LEADS_ALERT_PHONE")]);
    if (!authToken || !authorizedPhone) return xml("Dollar Leads texting is not configured yet.", 503);
    const form = new URLSearchParams(await req.text());
    if (!await validTwilioSignature(req.url, form, req.headers.get("x-twilio-signature") ?? "", authToken)) return xml("Unauthorized", 401);
    if (normalizePhone(form.get("From") ?? "") !== normalizePhone(authorizedPhone)) return xml("This number is not authorized.", 403);

    const match = (form.get("Body") ?? "").toUpperCase().match(/\bPAID\s+(DL-[A-Z0-9]{4,32})\b/);
    if (!match) return xml("Use: PAID DL-XXXXX");
    const code = match[1];
    const intakeQuery = new URLSearchParams({ source: "eq.dollar-leads-v1", notes: `ilike.*${code}*`, select: "id,name,email,markets,list_type,volume", limit: "1" });
    const intake = (await rest(`intake_requests?${intakeQuery}`))?.[0];
    if (!intake) return xml(`Order ${code} was not found.`);
    const marketDisplay = Array.isArray(intake.markets) ? intake.markets[0] : intake.markets;
    const laneDisplay = Array.isArray(intake.list_type) ? intake.list_type[0] : intake.list_type;
    const batchQuery = new URLSearchParams({ market_display: `eq.${marketDisplay}`, lane_display: `eq.${laneDisplay}`, status: "eq.live", select: "market,lane,cycle", limit: "1" });
    const batch = (await rest(`dollar_batches?${batchQuery}`))?.[0];
    if (!batch) return xml(`No live inventory remains for ${code}. Derrick has been alerted.`);
    const packSize = PACK_SIZES[intake.volume];
    if (!packSize) return xml(`Order ${code} has an unsupported pack size.`);

    const inserted = await rest("dollar_fulfillment_jobs?on_conflict=order_code", { method: "POST", headers: { Prefer: "return=representation,resolution=ignore-duplicates" }, body: JSON.stringify({ order_code: code, intake_request_id: intake.id, customer_name: intake.name, customer_email: intake.email, market: batch.market, market_display: marketDisplay, lane: batch.lane, lane_display: laneDisplay, pack_label: intake.volume, pack_size: packSize, cycle: batch.cycle, cycle_slug: cycleSlug(batch.cycle) }) });
    let job = inserted?.[0];
    if (!job) job = (await rest(`dollar_fulfillment_jobs?order_code=eq.${encodeURIComponent(code)}&select=*&limit=1`))?.[0];
    if (job?.status === "delivered") return xml(`${code} was already delivered.`);
    if (job?.status === "processing") return xml(`${code} is already being prepared.`);
    if (job?.status === "failed") return xml(`${code} needs attention before it can be resent.`);
    await rest("activity_feed", { method: "POST", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ event_type: "fulfillment:queued", source: "twilio", title: `${code} payment confirmed by Derrick`, body: `${packSize} ${laneDisplay} records for ${marketDisplay} queued for Danny fulfillment.`, target: "derrick" }) });
    return xml(`${code} payment confirmed. Danny is preparing and emailing the list now.`);
  } catch (error) {
    return xml(`Could not queue fulfillment: ${String((error as Error)?.message ?? error).slice(0, 160)}`, 500);
  }
});
