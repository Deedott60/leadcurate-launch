// Guarded internal reply sender for the Hermes Dollar Leads mail worker.
const SB_URL = Deno.env.get("SUPABASE_URL") ?? "https://jdmlsraqioigbukspduo.supabase.co";
const FROM_EMAIL = Deno.env.get("LEADCURATE_FROM_EMAIL") ?? "Dollar Leads <hello@leadcurate.com>";
const MAIL_BASE = Deno.env.get("HOSTINGER_MAIL_BASE_URL") ?? "https://api.mail.hostinger.com";
const JSON_HEADERS = { "Content-Type": "application/json" };
const RISK = /\b(refund|chargeback|dispute|cancel|cancellation|lawyer|attorney|legal|sue|lawsuit|fraud|scam|complaint|wrong list|change category|switch category|custom order|duplicate charge)\b/i;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: JSON_HEADERS });
}

function adminKey() {
  const direct = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (direct) return direct;
  const keys = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (!keys) return "";
  try { return JSON.parse(keys).default ?? ""; } catch { return ""; }
}

async function secret(name: string) {
  const key = adminKey();
  if (!key) return "";
  const res = await fetch(`${SB_URL}/rest/v1/rpc/get_app_secret`, {
    method: "POST",
    headers: { apikey: key, Authorization: `Bearer ${key}`, ...JSON_HEADERS },
    body: JSON.stringify({ secret_name: name }),
  });
  return res.ok ? await res.json() : "";
}

async function rest(path: string, init: RequestInit = {}) {
  const key = adminKey();
  if (!key) throw new Error("Supabase admin key is unavailable");
  const res = await fetch(`${SB_URL}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: key, Authorization: `Bearer ${key}`, ...JSON_HEADERS, ...(init.headers ?? {}) },
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`Supabase ${res.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

async function mailboxId(token: string) {
  const configured = await secret("HOSTINGER_MAILBOX_RESOURCE_ID");
  if (configured) return configured;
  const res = await fetch(`${MAIL_BASE}/api/v1/me`, { headers: { Authorization: `Bearer ${token}`, Accept: "application/json" } });
  if (!res.ok) return "";
  const payload = await res.json();
  return payload?.data?.mailboxes?.[0]?.resourceId ?? "";
}

function escapeHtml(text: string) {
  return text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function emailHtml(text: string) {
  const paragraphs = text.split(/\n\s*\n/).map((part) => `<p style="margin:0 0 14px;">${escapeHtml(part).replaceAll("\n", "<br>")}</p>`).join("");
  return `<div style="font-family:Arial,sans-serif;max-width:560px;color:#101418;line-height:1.6;"><div style="background:#101418;color:#fff;padding:16px 20px;border-radius:8px 8px 0 0;font-size:18px;font-weight:800;">DOLLAR<span style="color:#16a34a;">LEADS</span></div><div style="border:1px solid #e4e8ec;border-top:0;padding:20px;border-radius:0 0 8px 8px;">${paragraphs}</div></div>`;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ ok: false, error: "POST required" }, 405);
  try {
    const expected = await secret("HOSTINGER_WEBHOOK_SECRET");
    if (!expected || req.headers.get("x-leadcurate-agent-token") !== expected) {
      return json({ ok: false, error: "unauthorized" }, 401);
    }

    const payload = await req.json();
    const inboundId = String(payload.inbound_email_id ?? "").trim();
    const to = String(payload.to ?? "").trim().toLowerCase();
    const subject = String(payload.subject ?? "").trim();
    let body = String(payload.body ?? "").trim();
    if (!inboundId || !to || !subject || !body) return json({ ok: false, error: "inbound_email_id, to, subject, and body are required" }, 400);
    if (body.length > 2500) return json({ ok: false, error: "reply is too long" }, 400);
    if (/[—–]/.test(body)) return json({ ok: false, error: "reply contains a prohibited dash" }, 400);

    const inboundRows = await rest(`inbound_emails?id=eq.${encodeURIComponent(inboundId)}&select=id,from_addr,subject,preview,handled&limit=1`);
    const inbound = inboundRows?.[0];
    if (!inbound || String(inbound.from_addr).toLowerCase() !== to) return json({ ok: false, error: "inbound email does not match recipient" }, 400);
    if (inbound.handled) return json({ ok: false, error: "inbound email was already handled" }, 409);
    if (RISK.test(`${inbound.subject ?? ""}\n${inbound.preview ?? ""}`)) return json({ ok: false, error: "message requires human review" }, 409);

    const buyerRows = await rest(`intake_requests?source=eq.dollar-leads-v1&email=ilike.${encodeURIComponent(to)}&select=id&limit=1`);
    if (!buyerRows?.length) return json({ ok: false, error: "recipient is not a known Dollar Leads buyer" }, 403);

    if (!/The Dollar Leads Team\s*$/i.test(body)) body += "\n\nThe Dollar Leads Team";
    const token = await secret("HOSTINGER_MAIL_TOKEN");
    const mailbox = token ? await mailboxId(token) : "";
    if (!token || !mailbox) throw new Error("Hostinger Mail is not configured");

    const sendSubject = /^re:/i.test(subject) ? subject : `Re: ${subject}`;
    const sent = await fetch(`${MAIL_BASE}/api/v1/mailboxes/${encodeURIComponent(mailbox)}/send`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, ...JSON_HEADERS, Accept: "application/json" },
      body: JSON.stringify({
        to: [to],
        displayName: FROM_EMAIL.replace(/^(.+?)\s*<.*>$/, "$1"),
        subject: sendSubject,
        text: body,
        html: emailHtml(body),
      }),
    });
    if (sent.status !== 204) throw new Error(`Hostinger ${sent.status}: ${await sent.text()}`);

    await rest(`inbound_emails?id=eq.${encodeURIComponent(inboundId)}&handled=eq.false`, {
      method: "PATCH",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({ handled: true }),
    });
    await rest("activity_feed", {
      method: "POST",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({ event_type: "mail:outbound", source: "hermes-mail", title: `Routine reply sent to ${to}`, body: `Subject: ${sendSubject}`, target: "derrick" }),
    });
    return json({ ok: true, sent: true, inbound_email_id: inboundId });
  } catch (error) {
    return json({ ok: false, error: String((error as Error)?.message ?? error) }, 500);
  }
});
