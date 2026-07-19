// Dollar Leads order alert v3: fires on every new dollar-leads-v1 intake row.
// 1) emails the buyer their payment link, 2) alerts Derrick on personal +
// company email and by SMS when Twilio secrets are configured, 3) posts to the
// Conference Room. SMS is best-effort and never blocks the email path.

const SB_URL = Deno.env.get("SUPABASE_URL") ?? "https://jdmlsraqioigbukspduo.supabase.co";
const SB_KEY = Deno.env.get("SUPABASE_PUBLISHABLE_KEY") ?? Deno.env.get("SUPABASE_ANON_KEY") ?? "sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4";
const FROM_EMAIL = Deno.env.get("LEADCURATE_FROM_EMAIL") ?? "LeadCurate <hello@leadcurate.com>";
const HOSTINGER_MAIL_BASE_URL = Deno.env.get("HOSTINGER_MAIL_BASE_URL") ?? "https://api.mail.hostinger.com";
const ALERT_RECIPIENTS = ["dmcdonald5649@gmail.com", "hello@leadcurate.com"];
const CASHTAG = "Derrick607";

const AMOUNTS: Record<string, number> = {
  "Starter $5 (50 records)": 5,
  "Work $15 (250 records)": 15,
  "Full $25 (500 records)": 25,
  "Fresh Scrub $20 (20 records)": 20,
  "Founders Deal $50 (1,000 records)": 50,
};

function adminKey() {
  const direct = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (direct) return direct;
  const jsonKeys = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (!jsonKeys) return "";
  try { return JSON.parse(jsonKeys).default ?? ""; } catch { return ""; }
}

async function secret(name: string) {
  const key = adminKey();
  if (!key) return Deno.env.get(name) ?? "";
  const res = await fetch(`${SB_URL}/rest/v1/rpc/get_app_secret`, { method: "POST", headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json" }, body: JSON.stringify({ secret_name: name }) });
  if (!res.ok) return Deno.env.get(name) ?? "";
  return await res.json();
}

async function mailboxId(token: string) {
  const configured = await secret("HOSTINGER_MAILBOX_RESOURCE_ID");
  if (configured) return configured;
  const res = await fetch(`${HOSTINGER_MAIL_BASE_URL}/api/v1/me`, { headers: { Authorization: `Bearer ${token}`, Accept: "application/json" } });
  const payload = await res.json();
  return payload?.data?.mailboxes?.[0]?.resourceId ?? "";
}

async function sendMail(to: string[], subject: string, html: string) {
  const token = await secret("HOSTINGER_MAIL_TOKEN");
  const resource = await mailboxId(token);
  const body = { to, displayName: "Dollar Leads", subject, html, text: html.replace(/<[^>]+>/g, " ") };
  const res = await fetch(`${HOSTINGER_MAIL_BASE_URL}/api/v1/mailboxes/${resource}/send`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(body) });
  if (res.status !== 204) throw new Error(`Hostinger Mail ${res.status}: ${await res.text()}`);
}

async function sendSms(body: string) {
  const [sid, token, from, to] = await Promise.all([
    secret("TWILIO_ACCOUNT_SID"),
    secret("TWILIO_AUTH_TOKEN"),
    secret("TWILIO_FROM_NUMBER"),
    secret("DOLLAR_LEADS_ALERT_PHONE"),
  ]);
  if (!sid || !token || !from || !to) return false;

  const form = new URLSearchParams({ From: from, To: to, Body: body });
  const res = await fetch(`https://api.twilio.com/2010-04-01/Accounts/${encodeURIComponent(sid)}/Messages.json`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${btoa(`${sid}:${token}`)}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: form,
  });
  if (!res.ok) throw new Error(`Twilio ${res.status}: ${await res.text()}`);
  return true;
}

async function activity(title: string, body: string) {
  await fetch(`${SB_URL}/rest/v1/activity_feed`, { method: "POST", headers: { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}`, "Content-Type": "application/json", Prefer: "return=minimal" }, body: JSON.stringify({ event_type: "conf:status", source: "dollar-leads", title, body, target: "derrick" }) }).catch(() => {});
}

function esc(s: string) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

Deno.serve(async (req) => {
  try {
    const payload = await req.json();
    const rec = payload.record ?? payload;
    if ((rec.source ?? "") !== "dollar-leads-v1") {
      return new Response(JSON.stringify({ ok: true, skipped: "not a dollar-leads order" }), { headers: { "Content-Type": "application/json" } });
    }

    const name = rec.name ?? "there";
    const email = rec.email ?? "";
    const county = Array.isArray(rec.markets) ? rec.markets[0] : (rec.markets ?? "");
    const lane = Array.isArray(rec.list_type) ? rec.list_type[0] : (rec.list_type ?? "");
    const pack = rec.volume ?? "";
    const amount = AMOUNTS[pack] ?? 0;
    const notes = rec.notes ?? "";
    const code = (notes.match(/DL-[A-Z0-9]+/) ?? ["DL-UNKNOWN"])[0];
    const payUrl = `https://cash.app/$${CASHTAG}/${amount}`;

    // 1. Buyer payment email
    let buyerMailed = false;
    if (email) {
      const buyerHtml = `
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#101418;">
          <div style="background:#101418;color:#fff;padding:18px 22px;border-radius:10px 10px 0 0;">
            <span style="font-size:20px;font-weight:800;">DOLLAR<span style="color:#16a34a;">LEADS</span></span>
          </div>
          <div style="border:1px solid #e4e8ec;border-top:0;border-radius:0 0 10px 10px;padding:22px;">
            <p style="font-size:16px;">Hey ${esc(name)}, inventory is available for your selected market and category.</p>
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
              <tr><td style="padding:6px 0;color:#5b6672;">Order code</td><td style="padding:6px 0;font-weight:700;">${esc(code)}</td></tr>
              <tr><td style="padding:6px 0;color:#5b6672;">County</td><td style="padding:6px 0;font-weight:700;">${esc(county)}</td></tr>
              <tr><td style="padding:6px 0;color:#5b6672;">Category</td><td style="padding:6px 0;font-weight:700;">${esc(lane)}</td></tr>
              <tr><td style="padding:6px 0;color:#5b6672;">Pack</td><td style="padding:6px 0;font-weight:700;">${esc(pack)}</td></tr>
            </table>
            <p style="font-size:14px;margin:18px 0 8px;">Pay below and your file is on the way the same day.</p>
            <a href="${payUrl}" style="display:inline-block;background:#16a34a;color:#06220f;font-weight:800;padding:13px 22px;border-radius:8px;text-decoration:none;font-size:15px;">Pay $${amount} with Cash App</a>
            <p style="font-size:13px;color:#5b6672;margin-top:12px;">Important: put your order code <b>${esc(code)}</b> in the payment note so we can match it fast.</p>
            <p style="font-size:13px;color:#5b6672;">Questions? Just reply to this email.</p>
            <p style="font-size:13px;margin-top:18px;">The Dollar Leads Team<br><span style="color:#5b6672;">a LeadCurate company</span></p>
          </div>
        </div>`;
      await sendMail([email], `Your Dollar Leads order ${code}: one step left`, buyerHtml);
      buyerMailed = true;
    }

    // 2. Operator alert: payment email went out, watch Cash App now
    const sentAt = new Date().toLocaleString("en-US", { timeZone: "America/New_York", hour: "numeric", minute: "2-digit", month: "short", day: "numeric" });
    const derrickHtml = `
      <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
        <h2 style="color:#0d7a3f;">PAYMENT EMAIL SENT: watch Cash App now</h2>
        <p style="font-size:14px;">${buyerMailed ? `Buyer was emailed their $${amount} payment link at ${sentAt} ET.` : `Buyer gave no valid email; they only have the on-page payment button.`} Expect a Cash App payment of <b>$${amount}</b> with note <b>${esc(code)}</b>.</p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr><td style="padding:5px 0;color:#5b6672;">Code</td><td style="padding:5px 0;font-weight:700;">${esc(code)}</td></tr>
          <tr><td style="padding:5px 0;color:#5b6672;">Buyer</td><td style="padding:5px 0;font-weight:700;">${esc(name)} (${esc(email)})</td></tr>
          <tr><td style="padding:5px 0;color:#5b6672;">County</td><td style="padding:5px 0;font-weight:700;">${esc(county)}</td></tr>
          <tr><td style="padding:5px 0;color:#5b6672;">Category</td><td style="padding:5px 0;font-weight:700;">${esc(lane)}</td></tr>
          <tr><td style="padding:5px 0;color:#5b6672;">Pack</td><td style="padding:5px 0;font-weight:700;">${esc(pack)} = $${amount}</td></tr>
          <tr><td style="padding:5px 0;color:#5b6672;">Extra notes</td><td style="padding:5px 0;">${esc(notes)}</td></tr>
        </table>
        <p style="font-size:14px;margin-top:14px;"><b>When the payment lands:</b> tell Claude or Codex "${esc(code)} paid" and the pack gets cut and sent.</p>
      </div>`;
    await sendMail(ALERT_RECIPIENTS, `$${amount} incoming: ${code} | ${county} | ${lane}`, derrickHtml);

    const smsSent = await sendSms(`$${amount} incoming: ${code}. ${county}, ${lane}. Buyer: ${email || name}. Check Cash App.`).catch(() => false);

    // 3. Conference Room breadcrumb
    await activity(`Dollar Leads order ${code}: ${pack} in ${county}`, `${name} (${email}) ordered ${lane}. Payment email sent to buyer. ${smsSent ? "Text alert sent." : "Text alert not configured."} Waiting on $${amount} Cash App payment with note ${code}.`);

    return new Response(JSON.stringify({ ok: true, code, amount, buyerMailed, smsSent }), { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return new Response(JSON.stringify({ ok: false, error: String(e) }), { status: 500, headers: { "Content-Type": "application/json" } });
  }
});
