declare const Deno: {
  env: { get(name: string): string | undefined };
  serve(handler: (req: Request) => Response | Promise<Response>): void;
};

const SB_URL = Deno.env.get("SUPABASE_URL") ?? "https://jdmlsraqioigbukspduo.supabase.co";
const SB_KEY = Deno.env.get("SUPABASE_PUBLISHABLE_KEY") ?? Deno.env.get("SUPABASE_ANON_KEY") ?? "sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4";
const FROM_EMAIL = Deno.env.get("LEADCURATE_FROM_EMAIL") ?? "LeadCurate <hello@leadcurate.com>";
const HOSTINGER_MAIL_BASE_URL = Deno.env.get("HOSTINGER_MAIL_BASE_URL") ?? "https://api.mail.hostinger.com";

const headers = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers });
}

function esc(v: unknown) {
  return String(v ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function money(v: unknown) {
  return "$" + Number(v || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function pct(value: number, max: number) {
  return Math.max(3, Math.round((value / Math.max(1, max)) * 100));
}

function barRow(label: string, value: number, max: number, suffix = "") {
  return `<tr><td style="width:150px;padding:6px 8px;color:#475569;">${esc(label)}</td><td style="padding:6px 8px;"><div style="background:#f3eddf;border-radius:999px;height:12px;"><div style="width:${pct(value, max)}%;background:#15803d;height:12px;border-radius:999px;"></div></div></td><td style="width:90px;text-align:right;font-weight:700;color:#0f172a;">${esc(value.toLocaleString())}${suffix}</td></tr>`;
}

function shell(title: string, body: string) {
  return `<div style="margin:0;background:#faf7f2;padding:28px;font-family:Inter,Arial,sans-serif;color:#0f172a;"><table role="presentation" width="100%" style="max-width:760px;margin:0 auto;background:#fff;border:1px solid #e2dccf;border-radius:14px;overflow:hidden;"><tr><td style="padding:28px;background:#0f172a;color:#faf7f2;"><div style="font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:#86efac;">LeadCurate</div><h1 style="margin:8px 0 0;font-family:Georgia,serif;font-size:30px;">${esc(title)}</h1></td></tr><tr><td style="padding:28px;">${body}</td></tr><tr><td style="padding:18px 28px;background:#f3eddf;color:#475569;font-size:13px;">LeadCurate LLC - curated, scored property records for the market you asked for.</td></tr></table></div>`;
}

function statCards(p: any) {
  const cards = [["Records", p.total], ["HOT", p.hot], ["Absentee", p.absentee], ["Top equity", money(p.top_equity)]];
  return `<table width="100%" style="border-collapse:separate;border-spacing:8px;margin:16px 0;"><tr>${cards.map(([k, v]) => `<td style="border:1px solid #e2dccf;border-radius:10px;padding:14px;"><div style="font-size:11px;text-transform:uppercase;color:#475569;">${k}</div><div style="font-size:22px;font-weight:800;color:#15803d;">${v}</div></td>`).join("")}</tr></table>`;
}

function executiveStatRow(p: any) {
  const averageValue = p.avg_property_value ?? p.analytics?.avg_property_value ?? p.analytics?.average_value;
  const medianHeld = p.median_years_held ?? p.analytics?.median_years_held ?? p.analytics?.avg_years_held;
  const mailingCoverage = p.mailing_coverage ?? p.analytics?.mailing_coverage ?? p.analytics?.mailing_address_coverage;
  const stats = [
    ["Total records", Number(p.total || 0).toLocaleString()],
    ["Avg. property value", averageValue !== undefined ? money(averageValue) : "Source-backed"],
    ["Median years held", medianHeld !== undefined ? `${Number(medianHeld).toLocaleString()} yrs` : "Included where public"],
    ["Mailing coverage", mailingCoverage !== undefined ? `${Math.round(Number(mailingCoverage))}%` : "Included where public"],
  ];
  return `<table width="100%" style="border-collapse:separate;border-spacing:8px;margin:18px 0;"><tr>${stats.map(([label, value]) => `<td style="border:1px solid #e2dccf;background:#faf7f2;border-radius:10px;padding:14px;vertical-align:top;"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#475569;">${esc(label)}</div><div style="font-size:20px;font-weight:800;color:#0f172a;margin-top:4px;">${esc(value)}</div></td>`).join("")}</tr></table>`;
}

function sampleRows(rows: any[] = [], limit = 5) {
  const body = rows.slice(0, limit).map((r) => `<tr><td>${esc(r.owner ?? r.owner_name ?? "")}</td><td>${esc(r.address ?? r.property_address ?? "")}</td><td>${money(r.value ?? r.property_value ?? r.total_value ?? r.owed)}</td><td>${esc(r.motivation ?? r.signal ?? r.lane ?? "")}</td></tr>`).join("");
  return `<table width="100%" style="border-collapse:collapse;margin-top:12px;font-size:13px;"><tr style="background:#f3eddf;"><th align="left" style="padding:8px;">Owner</th><th align="left" style="padding:8px;">Property</th><th align="right" style="padding:8px;">Value / Owed</th><th align="left" style="padding:8px;">Signal</th></tr>${body.replaceAll("<td>", "<td style=\"border-bottom:1px solid #e2dccf;padding:8px;\">").replaceAll("<td>$", "<td style=\"border-bottom:1px solid #e2dccf;padding:8px;text-align:right;\">$")}</table>`;
}

function upsellBlock() {
  const links = [
    ["Verified Vacant Land", "https://leadcurate.com/sample-deliveries/"],
    ["Absentee", "https://leadcurate.com/sample-deliveries/"],
    ["Out-of-State", "https://leadcurate.com/sample-deliveries/"],
    ["Tax Delinquent", "https://leadcurate.com/sample-deliveries/"],
    ["Asset Locator", "https://leadcurate.com/sample-deliveries/charlotte-asset-locator-2026-07-06/"],
    ["County Intelligence", "https://leadcurate.com/sample-deliveries/"],
  ];
  return `<div style="margin-top:24px;padding:18px;border:1px solid #bbf7d0;background:#f0fdf4;border-radius:10px;"><div style="font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:#14532d;font-weight:800;">Available today</div><div style="margin-top:10px;display:block;line-height:2;">${links.map(([label, href]) => `<a href="${href}" style="display:inline-block;margin:0 8px 8px 0;color:#14532d;text-decoration:none;font-weight:800;">✓ ${esc(label)}</a>`).join("")}</div></div>`;
}

function sampleTable(sample: any[] = [], redact = false) {
  const rows = sample.slice(0, 8).map((r) => `<tr><td>${esc(redact ? redactName(r.owner) : r.owner)}</td><td>${esc(redact ? redactAddress(r.address) : r.address)}</td><td>${money(r.owed)}</td><td>${esc(r.motivation)}</td></tr>`).join("");
  return `<table width="100%" style="border-collapse:collapse;margin-top:16px;font-size:13px;"><tr style="background:#f3eddf;"><th align="left" style="padding:8px;">Owner</th><th align="left" style="padding:8px;">Property</th><th align="right" style="padding:8px;">Owed</th><th align="left" style="padding:8px;">Signal</th></tr>${rows.replaceAll("<td>", "<td style=\"border-bottom:1px solid #e2dccf;padding:8px;\">").replaceAll("<td>$", "<td style=\"border-bottom:1px solid #e2dccf;padding:8px;text-align:right;\">$")}</table>`;
}

function redactName(name = "") {
  return String(name).split(/\s+/).map((p) => /^(heirs|hrs)$/i.test(p) ? p : p ? p[0] + "***" : "").join(" ");
}

function redactAddress(addr = "") {
  return String(addr).replace(/\b\d{1,6}\b/, "###");
}

// ---- ONE canonical numbers/table renderer used by every lane. ----
// Lane differences come entirely from the DATA (p.numbers, p.sample field names),
// never from a different code path. This is deliberate: the whole reason
// emails looked different every time is that each lane got its own hand-built
// render function. There is exactly one now.

function numbersBlock(title: string, items: [string, string | number][]) {
  const rows = items.map(([label, value]) =>
    `<tr><td style="padding:10px 0;border-bottom:1px solid var(--line,#e2dccf);color:#475569;">${esc(label)}</td><td style="padding:10px 0;border-bottom:1px solid #e2dccf;text-align:right;font-weight:800;color:#0f172a;">${esc(value)}</td></tr>`
  ).join("");
  return `<h2 style="font-family:Georgia,serif;font-size:20px;margin:22px 0 6px;color:#0f172a;">${esc(title)}</h2><table width="100%" style="border-collapse:collapse;background:#faf7f2;border-radius:10px;padding:4px 16px;"><tbody>${rows}</tbody></table>`;
}

function heroStatCards(items: [string, string | number][]) {
  return `<table width="100%" style="border-collapse:separate;border-spacing:8px;margin:16px 0;"><tr>${items.map(([k, v]) => `<td style="border:1px solid #e2dccf;border-radius:10px;padding:14px;"><div style="font-size:11px;text-transform:uppercase;color:#475569;">${esc(k)}</div><div style="font-size:22px;font-weight:800;color:#15803d;">${esc(v)}</div></td>`).join("")}</tr></table>`;
}

// Derives the "value" column label + value from whichever field is present on a record,
// so the same table renderer works for a debt lane (owed) or a vacant-land lane (land_value) etc.
function recordValue(r: any): [string, string] {
  if (r.owed !== undefined) return ["Owed", money(r.owed)];
  if (r.land_value !== undefined) return ["Land Value", money(r.land_value)];
  if (r.value !== undefined || r.property_value !== undefined || r.total_value !== undefined) return ["Value", money(r.value ?? r.property_value ?? r.total_value)];
  return ["Value", "—"];
}

function genericSampleTable(sample: any[] = [], redact = false, limit = 8) {
  const valueLabel = sample.length ? recordValue(sample[0])[0] : "Value";
  const rows = sample.slice(0, limit).map((r) => {
    const owner = r.owner ?? r.owner_name ?? "";
    const address = r.address ?? r.property_address ?? "";
    const [, value] = recordValue(r);
    const extra = r.acreage !== undefined ? `${Number(r.acreage).toLocaleString()} ac` : (r.motivation ?? r.signal ?? "");
    return `<tr><td style="border-bottom:1px solid #e2dccf;padding:8px;">${esc(redact ? redactName(owner) : owner)}</td><td style="border-bottom:1px solid #e2dccf;padding:8px;">${esc(redact ? redactAddress(address) : address)}</td><td style="border-bottom:1px solid #e2dccf;padding:8px;text-align:right;">${esc(value)}</td><td style="border-bottom:1px solid #e2dccf;padding:8px;">${esc(extra)}</td></tr>`;
  }).join("");
  const extraLabel = sample.length && sample[0].acreage !== undefined ? "Acreage" : "Signal";
  return `<table width="100%" style="border-collapse:collapse;margin-top:12px;font-size:13px;"><tr style="background:#f3eddf;"><th align="left" style="padding:8px;">Owner</th><th align="left" style="padding:8px;">Property</th><th align="right" style="padding:8px;">${esc(valueLabel)}</th><th align="left" style="padding:8px;">${esc(extraLabel)}</th></tr>${rows}</table>`;
}

// Builds the "By the numbers" block generically from whatever the caller passed in
// p.numbers (array of [label, value] pairs, already formatted). If the caller didn't
// pass p.numbers, falls back to the common fields every lane tends to have.
function deriveNumbers(p: any): [string, string | number][] {
  if (Array.isArray(p.numbers) && p.numbers.length) return p.numbers;
  const out: [string, string | number][] = [["Total records", Number(p.total || 0).toLocaleString()]];
  if (p.hot !== undefined) out.push(["HOT records", Number(p.hot).toLocaleString()]);
  if (p.absentee !== undefined) out.push(["Absentee owners", Number(p.absentee).toLocaleString()]);
  if (p.top_equity !== undefined) out.push(["Top equity", money(p.top_equity)]);
  if (p.median_land_value !== undefined) out.push(["Median land value", money(p.median_land_value)]);
  if (p.avg_property_value !== undefined) out.push(["Avg. property value", money(p.avg_property_value)]);
  if (p.median_years_held !== undefined) out.push(["Median years held", `${p.median_years_held} yrs`]);
  return out;
}

function heroCards(p: any): [string, string | number][] {
  if (Array.isArray(p.hero_cards) && p.hero_cards.length) return p.hero_cards;
  const nums = deriveNumbers(p);
  return nums.slice(0, 4);
}

function renderSample(p: any) {
  const headline = p.opportunity_headline ?? `${esc(p.name)}, here is the redacted preview audit for ${esc(p.market)} / ${esc(p.lane)}.`;
  return shell(`Preview Audit: ${p.market}`, `<p style="font-size:16px;line-height:1.6;">${esc(headline)}</p>${heroStatCards(heroCards(p))}${numbersBlock("By the numbers", deriveNumbers(p))}${p.working_notes ? `<div style="padding:16px;background:#faf7f2;border-left:4px solid #15803d;margin:18px 0;"><strong>Working notes:</strong><br>${esc(p.working_notes)}</div>` : ""}<h2 style="font-size:18px;margin-top:22px;">Sample from the file</h2>${genericSampleTable(p.sample, true)}<div style="margin-top:22px;padding:18px;background:#15803d;color:white;border-radius:10px;text-align:center;"><a href="https://leadcurate.com/intake/" style="color:white;font-weight:800;text-decoration:none;">Reserve Your County</a></div>`);
}

function renderDelivery(p: any) {
  const headline = p.opportunity_headline ?? `${Number(p.total || 0).toLocaleString()} ${p.market} ${p.lane} records ready for investor outreach. Delivered today. Cleaned, verified, ready to market.`;
  const notes = p.working_notes ?? "Work the highest-scored records first. Prioritize owners with stronger motivation density, absentee signals, older hold periods, or larger value gaps before broad follow-up.";
  const strategy = p.outreach_strategy ?? "Suggested outreach: direct mail first for long-held or absentee records, then follow with a concise owner-specific second touch.";
  const summary = p.summary ?? `${p.name}, this is your paid LeadCurate delivery briefing for ${p.market} / ${p.lane}. The attached XLSX is the working file; this email gives you the one-page read on how to use it.`;
  return shell(`Delivery Briefing: ${p.market}`, `<div style="font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#15803d;font-weight:800;">Opportunity headline</div><h2 style="font-family:Georgia,serif;font-size:26px;line-height:1.2;margin:8px 0 14px;color:#0f172a;">${esc(headline)}</h2>${heroStatCards(heroCards(p))}<div style="margin:12px 0 20px;"><a href="${esc(p.list_url)}" style="display:inline-block;background:#15803d;color:white;text-decoration:none;font-weight:800;padding:12px 16px;border-radius:8px;">Download attached list</a></div><p style="font-size:16px;line-height:1.65;">${esc(summary)}</p>${numbersBlock("By the numbers", deriveNumbers(p))}<div style="padding:16px;background:#faf7f2;border-left:4px solid #15803d;margin:18px 0;"><strong>Working notes:</strong><br>${esc(notes)}</div><div style="padding:16px;background:#0f172a;color:#faf7f2;border-radius:10px;margin:18px 0;"><strong>Suggested outreach strategy:</strong> ${esc(strategy)}</div><h2 style="font-size:18px;margin-top:22px;">Five records from the file</h2>${genericSampleTable(p.sample, false, 5)}${upsellBlock()}<div style="margin-top:22px;padding:18px;background:#0f172a;color:white;border-radius:10px;"><strong>Your full XLSX is attached.</strong> Use this briefing as the work order; use the attachment as the source file.</div>`);
}

function renderComparison(p: any) {
  const markets = p.markets ?? [];
  const max = (field: string) => Math.max(1, ...markets.map((m: any) => Number(m[field] || 0)));
  const metric = (title: string, field: string, fmt = (n: number) => n.toLocaleString()) => `<h2>${esc(title)}</h2><table width="100%">${markets.map((m: any) => barRow(m.name || m.slug, Number(m[field] || 0), max(field), field.includes("equity") || field.includes("debt") ? "" : "")).join("").replace(/(<td style="width:90px[^>]*>)([^<]+)/g, (_m: string, a: string, b: string) => a + fmt(Number(String(b).replace(/,/g, ""))))}</table>`;
  return shell("Market Comparison Audit", `<p style="font-size:16px;line-height:1.6;">${esc(p.name)}, here is a side-by-side view of the counties you asked about.</p>${metric("Average Tax Debt", "avg_debt", money)}${metric("HOT Records", "hot")}${metric("Absentee Owners", "absentee")}${metric("Probate / Heirs Count", "heirs_count")}${metric("Top Equity", "top_equity", money)}<div style="margin-top:22px;padding:18px;background:#15803d;color:white;border-radius:10px;text-align:center;"><a href="https://leadcurate.com/intake/" style="color:white;font-weight:800;text-decoration:none;">Reserve any of these counties - $149 launch price</a></div>`);
}

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

async function activity(event_type: string, title: string, body: string, target = "derrick") {
  await fetch(`${SB_URL}/rest/v1/activity_feed`, { method: "POST", headers: { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}`, "Content-Type": "application/json", Prefer: "return=minimal" }, body: JSON.stringify({ event_type, source: "send-delivery", title, body, target }) }).catch(() => {});
}

async function mailboxId(token: string) {
  const configured = await secret("HOSTINGER_MAILBOX_RESOURCE_ID");
  if (configured) return configured;
  const res = await fetch(`${HOSTINGER_MAIL_BASE_URL}/api/v1/me`, { headers: { Authorization: `Bearer ${token}`, Accept: "application/json" } });
  const payload = await res.json();
  return payload?.data?.mailboxes?.[0]?.resourceId ?? "";
}

async function sendMail(to: string, subject: string, html: string, attachment?: { filename: string; content: string }) {
  const token = await secret("HOSTINGER_MAIL_TOKEN");
  const resource = await mailboxId(token);
  const body: any = { to: [to], displayName: FROM_EMAIL.replace(/^(.+?)\s*<.*>$/, "$1"), subject, html, text: html.replace(/<[^>]+>/g, " ") };
  if (attachment) body.attachments = [{ filename: attachment.filename, content: attachment.content, contentType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }];
  const res = await fetch(`${HOSTINGER_MAIL_BASE_URL}/api/v1/mailboxes/${resource}/send`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(body) });
  if (res.status !== 204) throw new Error(`Hostinger Mail ${res.status}: ${await res.text()}`);
}

async function verifyBeforeSend(payload: any) {
  const expected = { total: payload.total, hot: payload.hot, warm: payload.warm, absentee: payload.absentee, top_equity: payload.top_equity, heirs_count: payload.analytics?.heirs_count ?? payload.heirs_count ?? 0, lane: payload.lane, market: payload.market, allow_entities: payload.allow_entities ?? false };
  const res = await fetch(`${SB_URL}/functions/v1/verify-delivery`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ list_url: payload.list_url, expected, llm_review: payload.llm_review ?? false }) });
  return await res.json();
}

async function fetchDeliveryFile(listUrl: string) {
  const attempts = [listUrl];
  try {
    const url = new URL(listUrl);
    if (url.hostname === "leadcurate.com" || url.hostname === "www.leadcurate.com") {
      attempts.push(`https://deedott60.github.io/leadcurate-launch${url.pathname}`);
    }
  } catch {
    // Let fetch surface the invalid URL error below.
  }
  let lastError = "";
  for (const url of attempts) {
    try {
      const file = await fetch(url);
      if (file.ok) return file;
      lastError = `${url}: ${file.status}`;
    } catch (err) {
      lastError = `${url}: ${String((err as Error)?.message ?? err)}`;
    }
  }
  throw new Error(`list_url fetch failed: ${lastError}`);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers });
  if (req.method !== "POST") return json({ ok: false, error: "POST required" }, 405);
  try {
    const p = await req.json();
    const mode = p.mode ?? "delivery";
    if (!p.to || !p.name) return json({ ok: false, error: "to and name are required" }, 400);
    let html = "";
    let subject = "";
    let attachment: { filename: string; content: string } | undefined;
    if (mode === "comparison") {
      subject = "LeadCurate market comparison audit";
      html = renderComparison(p);
    } else if (mode === "sample") {
      subject = `LeadCurate sample audit: ${p.market}`;
      html = renderSample(p);
    } else if (mode === "delivery") {
      if (!p.list_url) return json({ ok: false, error: "delivery mode requires list_url" }, 400);
      const verified = await verifyBeforeSend(p);
      if (!verified.ok) {
        await activity("conf:blocker", "Delivery verification failed", JSON.stringify(verified.failures ?? verified, null, 2));
        return json({ ok: false, error: "delivery verification failed", verify: verified }, 400);
      }
      const file = await fetchDeliveryFile(String(p.list_url));
      const bytes = new Uint8Array(await file.arrayBuffer());
      let binary = "";
      for (const b of bytes) binary += String.fromCharCode(b);
      attachment = { filename: p.filename ?? p.list_url.split("/").pop() ?? "LeadCurate-delivery.xlsx", content: btoa(binary) };
      subject = `LeadCurate delivery audit: ${p.market}`;
      html = renderDelivery(p);
    } else {
      return json({ ok: false, error: `Unknown mode ${mode}` }, 400);
    }
    await sendMail(p.to, subject, html, attachment);
    await activity(mode === "delivery" ? "delivery:sent" : mode === "comparison" ? "comparison:sent" : "sample:sent", `${subject} sent`, `${p.name} <${p.to}>`);
    return json({ ok: true, mode, sent: true });
  } catch (err) {
    await activity("conf:blocker", "send-delivery failed", String((err as Error)?.message ?? err));
    return json({ ok: false, error: String((err as Error)?.message ?? err) }, 500);
  }
});
