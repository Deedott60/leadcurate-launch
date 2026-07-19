const SB_URL = Deno.env.get("SUPABASE_URL") ?? "https://jdmlsraqioigbukspduo.supabase.co";
const JSON_HEADERS = { "Content-Type": "application/json" };
const PACK_SIZES: Record<string, number> = {
  "Starter $5 (50 records)": 50,
  "Work $15 (250 records)": 250,
  "Full $25 (500 records)": 500,
  "Fresh Scrub $20 (20 records)": 20,
  "Founders Deal $50 (1,000 records)": 1000,
};

function json(body: unknown, status = 200) { return new Response(JSON.stringify(body), { status, headers: JSON_HEADERS }); }

function adminKey() {
  const direct = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (direct) return direct;
  try { return JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}").default ?? ""; } catch { return ""; }
}

async function secret(name: string) {
  const key = adminKey();
  if (!key) return "";
  const res = await fetch(`${SB_URL}/rest/v1/rpc/get_app_secret`, { method: "POST", headers: { apikey: key, Authorization: `Bearer ${key}`, ...JSON_HEADERS }, body: JSON.stringify({ secret_name: name }) });
  return res.ok ? await res.json() : "";
}

async function rest(path: string, init: RequestInit = {}) {
  const key = adminKey();
  const res = await fetch(`${SB_URL}/rest/v1/${path}`, { ...init, headers: { apikey: key, Authorization: `Bearer ${key}`, ...JSON_HEADERS, ...(init.headers ?? {}) } });
  const text = await res.text();
  if (!res.ok) throw new Error(`Supabase ${res.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

async function sendTelegram(body: string) {
  const [token, chatId] = await Promise.all([secret("TELEGRAM_BOT_TOKEN"), secret("TELEGRAM_HOME_CHANNEL")]);
  if (!token || !chatId) return false;
  const res = await fetch(`https://api.telegram.org/bot${encodeURIComponent(token)}/sendMessage`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ chat_id: chatId, text: body }) });
  return res.ok;
}

async function job(id: string) {
  return (await rest(`dollar_fulfillment_jobs?id=eq.${encodeURIComponent(id)}&select=*&limit=1`))?.[0];
}

function cycleSlug(cycle: string) {
  const parsed = new Date(`1 ${cycle} UTC`);
  if (Number.isNaN(parsed.getTime())) throw new Error(`Cannot parse cycle ${cycle}`);
  return `${parsed.getUTCFullYear()}-${String(parsed.getUTCMonth() + 1).padStart(2, "0")}`;
}

async function confirmPaid(orderCode: string) {
  const code = orderCode.trim().toUpperCase();
  if (!/^DL-[A-Z0-9]{4,32}$/.test(code)) throw new Error("Use a valid DL-XXXXX order code");
  const intakeQuery = new URLSearchParams({ source: "eq.dollar-leads-v1", notes: `ilike.*${code}*`, select: "id,name,email,markets,list_type,volume", limit: "1" });
  const intake = (await rest(`intake_requests?${intakeQuery}`))?.[0];
  if (!intake) throw new Error(`Order ${code} was not found`);
  const marketDisplay = Array.isArray(intake.markets) ? intake.markets[0] : intake.markets;
  const laneDisplay = Array.isArray(intake.list_type) ? intake.list_type[0] : intake.list_type;
  const batchQuery = new URLSearchParams({ market_display: `eq.${marketDisplay}`, lane_display: `eq.${laneDisplay}`, status: "eq.live", select: "market,lane,cycle", limit: "1" });
  const batch = (await rest(`dollar_batches?${batchQuery}`))?.[0];
  if (!batch) throw new Error(`No live inventory remains for ${code}`);
  const packSize = PACK_SIZES[intake.volume];
  if (!packSize) throw new Error(`Order ${code} has an unsupported pack size`);

  const inserted = await rest("dollar_fulfillment_jobs?on_conflict=order_code", { method: "POST", headers: { Prefer: "return=representation,resolution=ignore-duplicates" }, body: JSON.stringify({ order_code: code, intake_request_id: intake.id, customer_name: intake.name, customer_email: intake.email, market: batch.market, market_display: marketDisplay, lane: batch.lane, lane_display: laneDisplay, pack_label: intake.volume, pack_size: packSize, cycle: batch.cycle, cycle_slug: cycleSlug(batch.cycle) }) });
  let queued = inserted?.[0];
  if (!queued) queued = (await rest(`dollar_fulfillment_jobs?order_code=eq.${encodeURIComponent(code)}&select=*&limit=1`))?.[0];
  if (!queued) throw new Error(`Could not queue ${code}`);
  if (inserted?.[0]) {
    await rest("activity_feed", { method: "POST", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ event_type: "fulfillment:queued", source: "telegram", title: `${code} payment confirmed by Derrick`, body: `${packSize} ${laneDisplay} records for ${marketDisplay} queued for Danny fulfillment.`, target: "derrick" }) });
  }
  return queued;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ ok: false, error: "POST required" }, 405);
  try {
    const expected = await secret("HOSTINGER_WEBHOOK_SECRET");
    if (!expected || req.headers.get("x-leadcurate-agent-token") !== expected) return json({ ok: false, error: "unauthorized" }, 401);
    const p = await req.json();

    if (p.action === "confirm_paid") {
      const queued = await confirmPaid(String(p.order_code ?? ""));
      return json({ ok: true, job: queued });
    }

    if (p.action === "claim") {
      const claimed = await rest("rpc/claim_dollar_fulfillment_job", { method: "POST", body: "{}" });
      return json({ ok: true, job: claimed?.id ? claimed : null });
    }

    if (p.action === "next_batch") {
      const current = await job(String(p.job_id));
      if (!current || current.status !== "processing") return json({ ok: false, error: "processing job not found" }, 404);
      const query = new URLSearchParams({ market: `eq.${current.market}`, lane: `eq.${current.lane}`, cycle: `eq.${current.cycle}`, status: "eq.live", select: "batch_no,seats_sold,seats_total", order: "batch_no.asc" });
      const rows = await rest(`dollar_batches?${query}`) ?? [];
      let batchNo = 0;
      if (current.pack_size === 1000) {
        const open = new Set(rows.filter((r: any) => Number(r.seats_sold) === 0).map((r: any) => Number(r.batch_no)));
        batchNo = [...open].sort((a: number, b: number) => a - b).find((n: number) => open.has(n + 1)) ?? 0;
      } else {
        batchNo = Number(rows.find((r: any) => Number(r.seats_sold) < Number(r.seats_total))?.batch_no ?? 0);
      }
      if (!batchNo) return json({ ok: false, error: "no eligible batch remains" }, 409);
      return json({ ok: true, batch_no: batchNo });
    }

    if (p.action === "reserve") {
      const current = await job(String(p.job_id));
      if (!current || current.status !== "processing") return json({ ok: false, error: "processing job not found" }, 404);
      const batchNo = Number(p.batch_no);
      const rpc = current.pack_size === 1000 ? "reserve_dollar_founders_batches" : "reserve_dollar_batch";
      const payload = current.pack_size === 1000
        ? { p_market: current.market, p_lane: current.lane, p_start_batch_no: batchNo, p_cycle: current.cycle }
        : { p_market: current.market, p_lane: current.lane, p_batch_no: batchNo, p_cycle: current.cycle };
      const reserved = await rest(`rpc/${rpc}`, { method: "POST", body: JSON.stringify(payload) });
      await rest(`dollar_fulfillment_jobs?id=eq.${encodeURIComponent(current.id)}`, { method: "PATCH", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ batch_no: batchNo, updated_at: new Date().toISOString() }) });
      return json({ ok: true, reservation: reserved });
    }

    if (p.action === "complete") {
      const current = await job(String(p.job_id));
      if (!current) return json({ ok: false, error: "job not found" }, 404);
      await rest(`dollar_fulfillment_jobs?id=eq.${encodeURIComponent(current.id)}`, { method: "PATCH", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ status: "delivered", delivery_dir: String(p.delivery_dir), delivered_at: new Date().toISOString(), updated_at: new Date().toISOString(), error: null }) });
      await rest("activity_feed", { method: "POST", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ event_type: "delivery:sent", source: "dollar-fulfillment", title: `Dollar Leads ${current.order_code} delivered`, body: `${current.pack_size} ${current.lane_display} records emailed to ${current.customer_email}. Batch ${current.batch_no ?? p.batch_no}.`, target: "derrick" }) });
      const telegramSent = await sendTelegram(`DELIVERED ${current.order_code}. ${current.pack_size} records emailed to ${current.customer_email}.`);
      return json({ ok: true, telegram_sent: telegramSent });
    }

    if (p.action === "fail") {
      const current = await job(String(p.job_id));
      if (!current) return json({ ok: false, error: "job not found" }, 404);
      const message = String(p.error ?? "unknown fulfillment error").slice(0, 1000);
      await rest(`dollar_fulfillment_jobs?id=eq.${encodeURIComponent(current.id)}`, { method: "PATCH", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ status: "failed", error: message, updated_at: new Date().toISOString() }) });
      await rest("activity_feed", { method: "POST", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ event_type: "conf:blocker", source: "dollar-fulfillment", title: `Dollar Leads ${current.order_code} needs attention`, body: message, target: "derrick" }) });
      const telegramSent = await sendTelegram(`NEEDS YOU ${current.order_code}. Delivery failed. Check the Dollar Leads dashboard.`);
      return json({ ok: true, telegram_sent: telegramSent });
    }
    return json({ ok: false, error: "unknown action" }, 400);
  } catch (error) {
    return json({ ok: false, error: String((error as Error)?.message ?? error) }, 500);
  }
});
