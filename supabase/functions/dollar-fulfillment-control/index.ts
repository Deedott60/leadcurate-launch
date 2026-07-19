const SB_URL = Deno.env.get("SUPABASE_URL") ?? "https://jdmlsraqioigbukspduo.supabase.co";
const JSON_HEADERS = { "Content-Type": "application/json" };

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

async function sendSms(body: string) {
  const [sid, token, from, to] = await Promise.all([secret("TWILIO_ACCOUNT_SID"), secret("TWILIO_AUTH_TOKEN"), secret("TWILIO_FROM_NUMBER"), secret("DOLLAR_LEADS_ALERT_PHONE")]);
  if (!sid || !token || !from || !to) return false;
  const form = new URLSearchParams({ From: from, To: to, Body: body });
  const res = await fetch(`https://api.twilio.com/2010-04-01/Accounts/${encodeURIComponent(sid)}/Messages.json`, { method: "POST", headers: { Authorization: `Basic ${btoa(`${sid}:${token}`)}`, "Content-Type": "application/x-www-form-urlencoded" }, body: form });
  return res.ok;
}

async function job(id: string) {
  return (await rest(`dollar_fulfillment_jobs?id=eq.${encodeURIComponent(id)}&select=*&limit=1`))?.[0];
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ ok: false, error: "POST required" }, 405);
  try {
    const expected = await secret("HOSTINGER_WEBHOOK_SECRET");
    if (!expected || req.headers.get("x-leadcurate-agent-token") !== expected) return json({ ok: false, error: "unauthorized" }, 401);
    const p = await req.json();

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
      const smsSent = await sendSms(`DELIVERED ${current.order_code}. ${current.pack_size} records emailed to ${current.customer_email}.`);
      return json({ ok: true, sms_sent: smsSent });
    }

    if (p.action === "fail") {
      const current = await job(String(p.job_id));
      if (!current) return json({ ok: false, error: "job not found" }, 404);
      const message = String(p.error ?? "unknown fulfillment error").slice(0, 1000);
      await rest(`dollar_fulfillment_jobs?id=eq.${encodeURIComponent(current.id)}`, { method: "PATCH", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ status: "failed", error: message, updated_at: new Date().toISOString() }) });
      await rest("activity_feed", { method: "POST", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ event_type: "conf:blocker", source: "dollar-fulfillment", title: `Dollar Leads ${current.order_code} needs attention`, body: message, target: "derrick" }) });
      const smsSent = await sendSms(`NEEDS YOU ${current.order_code}. Delivery failed. Check the Dollar Leads dashboard.`);
      return json({ ok: true, sms_sent: smsSent });
    }
    return json({ ok: false, error: "unknown action" }, 400);
  } catch (error) {
    return json({ ok: false, error: String((error as Error)?.message ?? error) }, 500);
  }
});
