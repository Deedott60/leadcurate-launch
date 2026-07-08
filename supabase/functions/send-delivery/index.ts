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

// Gmail/Outlook ignore CSS margin:auto on tables about half the time. The only
// reliable way to center an email body is an outer 100%-wide table with
// align="center" (HTML attribute, not CSS) wrapping a fixed-width inner table.
function shell(eyebrow: string, title: string, greetingName: string, greetingLine: string, body: string) {
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#faf7f2;padding:32px 16px;font-family:Arial,sans-serif;"><tr><td align="center">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" align="center" style="max-width:640px;width:100%;background:#ffffff;border:1px solid #e2dccf;border-radius:14px;overflow:hidden;">
<tr><td style="padding:28px 32px 8px;">
  <table role="presentation" cellpadding="0" cellspacing="0"><tr>
    <td style="width:36px;height:36px;background:#15803d;border-radius:8px;text-align:center;vertical-align:middle;"><span style="color:#fff;font-family:Georgia,serif;font-weight:700;font-size:20px;">L</span></td>
    <td style="padding-left:10px;font-family:Georgia,serif;font-weight:700;font-size:20px;color:#0f172a;vertical-align:middle;">LeadCurate</td>
  </tr></table>
</td></tr>
<tr><td style="padding:8px 32px 0;">
  <div style="font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#15803d;">${esc(eyebrow)}</div>
  <h1 style="font-family:Georgia,serif;font-size:26px;line-height:1.2;color:#0f172a;margin:8px 0 12px;">${esc(title)}</h1>
  <p style="font-size:15px;line-height:1.6;color:#334155;margin:0 0 4px;">${esc(greetingName)},</p>
  <p style="font-size:15px;line-height:1.6;color:#334155;margin:0 0 4px;">${esc(greetingLine)}</p>
</td></tr>
${body}
<tr><td style="padding:20px 32px;background:#f3eddf;font-size:13px;color:#475569;">Any questions, just reply.<br><br><strong>Derrick</strong><br>LeadCurate<br><a href="mailto:hello@leadcurate.com" style="color:#15803d;">hello@leadcurate.com</a></td></tr>
</table>
</td></tr></table>`;
}

function section(inner: string) {
  return `<tr><td style="padding:22px 32px 0;">${inner}</td></tr>`;
}

function boxedRows(rows: string[]) {
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2dccf;border-radius:10px;">${rows.join("")}</table>`;
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
  const rows = items.map(([label, value], i) =>
    `<tr><td style="padding:10px 16px;${i < items.length - 1 ? "border-bottom:1px solid #e2dccf;" : ""}font-size:14px;color:#475569;">${esc(label)}</td><td style="padding:10px 16px;${i < items.length - 1 ? "border-bottom:1px solid #e2dccf;" : ""}font-size:14px;font-weight:800;color:#0f172a;text-align:right;">${esc(value)}</td></tr>`
  ).join("");
  return `<h2 style="font-family:Georgia,serif;font-size:18px;color:#0f172a;margin:0 0 6px;">${esc(title)}</h2>${boxedRows([rows])}`;
}

// cellspacing + percentage-width <td> is a known email-client trap: Gmail/Outlook
// don't subtract spacing from the percentage math, so the row silently overflows
// the 640px container and shoves right/wraps on a phone screen. Real spacer
// cells (fixed px, no percentage) are the bulletproof fix.
function heroStatCards(items: [string, string | number][]) {
  const cell = ([k, v]: [string, string | number]) => `<td style="border:1px solid #e2dccf;border-radius:10px;padding:14px;background:#faf7f2;"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:#64748b;font-weight:700;">${esc(k)}</div><div style="font-size:20px;font-weight:800;color:#0f172a;margin-top:4px;">${esc(v)}</div></td>`;
  const spacer = `<td width="8"></td>`;
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>${items.map(cell).join(spacer)}</tr></table>`;
}

// The actual differentiation reasoning, generic across lanes: WHY a rebuilt/verified
// file beats a static purchased one. Caller can override entirely via p.differentiators
// (array of [heading, body]); falls back to lane-flavored defaults otherwise so this
// section is never empty and never just "we use fresh data."
const LANE_DEFAULT_DIFFERENTIATORS: Record<string, [string, string][]> = {
  verified_vacant_land: [
    ["Rebuilt from the current county file", "not resold from a stockpile that could be a year or more old."],
    ["Cross-checked before it ships", "the county's own vacancy and improvement fields get verified, not taken at face value."],
    ["Absentee owners flagged specifically", "these owners are structurally more likely to sell than build or hold."],
    ["Refreshed on request", "sold once and left to rot is the opposite of how this works."],
  ],
  default: [
    ["Pulled directly from the county's source records", "not aggregated from a third-party reseller with unknown lag."],
    ["Deduplicated and lane-matched", "the file only contains what you actually ordered, one row per property."],
    ["Verified before it ships", "stats in this email are computed from the same file you're getting, not hand-typed."],
    ["Refreshed on request", "this isn't a static download you're stuck with once purchased."],
  ],
};

function differentiatorsBlock(p: any) {
  const items: [string, string][] = Array.isArray(p.differentiators) && p.differentiators.length
    ? p.differentiators
    : (LANE_DEFAULT_DIFFERENTIATORS[String(p.lane ?? "")] ?? LANE_DEFAULT_DIFFERENTIATORS.default);
  const rows = items.map(([head, tail], i) =>
    `<tr><td style="padding:12px 16px;${i < items.length - 1 ? "border-bottom:1px solid #e2dccf;" : ""}font-size:14px;color:#334155;"><strong style="color:#0f172a;">${esc(head)}</strong> — ${esc(tail)}</td></tr>`
  ).join("");
  return `<h2 style="font-family:Georgia,serif;font-size:18px;color:#0f172a;margin:0 0 10px;">Why this beats a purchased list</h2>${boxedRows([rows])}`;
}

// Derives the "value" column label + value from whichever field is present on a record,
// so the same table renderer works for a debt lane (owed) or a vacant-land lane (land_value) etc.
function recordValue(r: any): [string, string] {
  if (r.owed !== undefined) return ["Owed", money(r.owed)];
  if (r.land_value !== undefined) return ["Land Value", money(r.land_value)];
  if (r.value !== undefined || r.property_value !== undefined || r.total_value !== undefined) return ["Value", money(r.value ?? r.property_value ?? r.total_value)];
  return ["Value", "—"];
}

function badge(label: string, bg: string, fg: string) {
  return `<span style="display:inline-block;background:${bg};color:${fg};font-size:10px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;padding:3px 8px;border-radius:999px;">${esc(label)}</span>`;
}

// Matches the real, previously-proven table design: green header row, owner name
// with an ABSENTEE badge inline when flagged, a colored STATUS pill per row.
// Works for any lane because it reads whatever fields recordValue()/status find.
function recordStatus(r: any): [string, string, string] {
  if (r.motivation === "HOT" || r.status === "HOT") return ["HOT", "#fee2e2", "#991b1b"];
  if (r.motivation === "WARM" || r.status === "WARM") return ["WARM", "#fef3c7", "#b45309"];
  if (r.vacant_signal || r.lane === "verified_vacant_land" || r.land_value !== undefined) return ["VACANT", "#dff4e8", "#15803d"];
  return ["ACTIVE", "#dff4e8", "#15803d"];
}

function genericSampleTable(sample: any[] = [], redact = false, limit = 8) {
  const secondaryLabel = sample.length && sample[0].acreage !== undefined ? "Acreage" : (sample.length && sample[0].equity !== undefined ? "Equity" : null);
  const rows = sample.slice(0, limit).map((r, i) => {
    const owner = r.owner ?? r.owner_name ?? "";
    const address = r.address ?? r.property_address ?? "";
    const [, value] = recordValue(r);
    const secondary = r.acreage !== undefined ? `${Number(r.acreage).toLocaleString()} ac` : (r.equity !== undefined ? money(r.equity) : "");
    const [statusLabel, statusBg, statusFg] = recordStatus(r);
    const ownerCell = `${esc(redact ? redactName(owner) : owner)}${r.is_absentee_owner === "yes" || r.absentee ? `<br>${badge("Absentee", "#dbeafe", "#1d4ed8")}` : ""}`;
    return `<tr><td style="border-bottom:1px solid #e2dccf;padding:10px 8px;color:#94a3b8;font-size:12px;">${i + 1}</td><td style="border-bottom:1px solid #e2dccf;padding:10px 8px;font-weight:700;">${ownerCell}</td><td style="border-bottom:1px solid #e2dccf;padding:10px 8px;">${esc(redact ? redactAddress(address) : address)}</td><td style="border-bottom:1px solid #e2dccf;padding:10px 8px;text-align:right;font-weight:700;">${esc(value)}</td>${secondaryLabel ? `<td style="border-bottom:1px solid #e2dccf;padding:10px 8px;text-align:right;color:#15803d;font-weight:700;">${esc(secondary)}</td>` : ""}<td style="border-bottom:1px solid #e2dccf;padding:10px 8px;text-align:center;">${badge(statusLabel, statusBg, statusFg)}</td></tr>`;
  }).join("");
  const valueLabel = sample.length ? recordValue(sample[0])[0] : "Value";
  return `<table width="100%" style="border-collapse:collapse;margin-top:12px;font-size:13px;"><tr style="background:#15803d;color:#ffffff;"><th align="left" style="padding:10px 8px;font-size:11px;text-transform:uppercase;">#</th><th align="left" style="padding:10px 8px;font-size:11px;text-transform:uppercase;">Owner</th><th align="left" style="padding:10px 8px;font-size:11px;text-transform:uppercase;">Address</th><th align="right" style="padding:10px 8px;font-size:11px;text-transform:uppercase;">${esc(valueLabel)}</th>${secondaryLabel ? `<th align="right" style="padding:10px 8px;font-size:11px;text-transform:uppercase;">${esc(secondaryLabel)}</th>` : ""}<th align="center" style="padding:10px 8px;font-size:11px;text-transform:uppercase;">Status</th></tr>${rows}</table>`;
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
  return nums.slice(1, 4); // skip "Total records" here, it's already in the headline
}

function ctaSection(label: string, href: string) {
  return section(`<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:0 0 10px;"><a href="${esc(href)}" style="display:inline-block;background:#15803d;color:#ffffff;text-decoration:none;font-weight:800;padding:14px 28px;border-radius:8px;font-size:15px;">${esc(label)}</a></td></tr></table>`);
}

function renderSample(p: any) {
  const eyebrow = `Preview Audit · ${p.lane ? String(p.lane).replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()) : "Curated List"}`;
  const greeting = p.opportunity_headline ?? "Here's the real answer to what makes this different from a static purchased list.";
  const fullAuditBox = p.audit_url
    ? section(`<div style="padding:22px;background:#0f172a;border-radius:12px;text-align:center;"><div style="color:#ffffff;font-family:Georgia,serif;font-size:20px;font-weight:700;margin-bottom:6px;">Your full breakdown is ready</div><div style="color:#cbd5e1;font-size:13px;margin-bottom:16px;">Full market audit, records, and geography — no customer data, just the real picture of what's available.</div><a href="${esc(p.audit_url)}" style="display:inline-block;background:#15803d;color:#ffffff;text-decoration:none;font-weight:800;padding:12px 24px;border-radius:8px;font-size:14px;">Open Full Audit →</a></div>`)
    : ctaSection("Reserve Your County", "https://leadcurate.com/intake/");
  const body = [
    section(heroStatCards(heroCards(p))),
    section(differentiatorsBlock(p)),
    section(`<h2 style="font-family:Georgia,serif;font-size:18px;color:#0f172a;margin:0 0 6px;">Sample from the file</h2><p style="font-size:13px;color:#64748b;margin:0 0 4px;">A few real trigger examples below — the full file is in your audit, not attached here.</p>${genericSampleTable(p.sample, true, 5)}`),
    fullAuditBox,
  ].join("");
  return shell(eyebrow, `${p.market}`, p.name, greeting, body);
}

function renderDelivery(p: any) {
  const eyebrow = `Delivery Briefing · ${p.lane ? String(p.lane).replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()) : "Curated List"}`;
  const greeting = p.summary ?? `Your order is delivered. The full XLSX is attached to this email.`;
  const notes = p.working_notes ?? "Work the highest-scored records first. Prioritize owners with stronger motivation density, absentee signals, older hold periods, or larger value gaps before broad follow-up.";
  const strategy = p.outreach_strategy ?? "Direct mail first for long-held or absentee records, then follow with a concise owner-specific second touch.";
  const body = [
    section(heroStatCards(heroCards(p))),
    p.list_url ? ctaSection("Download attached list", p.list_url) : "",
    section(differentiatorsBlock(p)),
    section(numbersBlock("By the numbers", deriveNumbers(p))),
    section(`<h2 style="font-family:Georgia,serif;font-size:18px;color:#0f172a;margin:0 0 6px;">Working notes</h2>${boxedRows([`<tr><td style="padding:12px 16px;font-size:14px;color:#334155;">${esc(notes)}</td></tr>`])}`),
    section(`<h2 style="font-family:Georgia,serif;font-size:18px;color:#0f172a;margin:0 0 6px;">Suggested outreach strategy</h2>${boxedRows([`<tr><td style="padding:12px 16px;font-size:14px;color:#334155;">${esc(strategy)}</td></tr>`])}`),
    section(`<h2 style="font-family:Georgia,serif;font-size:18px;color:#0f172a;margin:0 0 6px;">Five records from the file</h2>${genericSampleTable(p.sample, false, 5)}`),
    section(upsellBlock()),
    section(`<div style="padding:16px;background:#0f172a;color:#faf7f2;border-radius:10px;"><strong>Your full XLSX is attached.</strong> Use this briefing as the work order; use the attachment as the source file.</div>`),
  ].join("");
  return shell(eyebrow, `${p.market}`, p.name, greeting, body);
}

function renderComparison(p: any) {
  const markets = p.markets ?? [];
  const max = (field: string) => Math.max(1, ...markets.map((m: any) => Number(m[field] || 0)));
  const metric = (title: string, field: string, fmt = (n: number) => n.toLocaleString()) => `<h2 style="font-family:Georgia,serif;font-size:16px;color:#0f172a;margin:14px 0 6px;">${esc(title)}</h2><table width="100%">${markets.map((m: any) => barRow(m.name || m.slug, Number(m[field] || 0), max(field), field.includes("equity") || field.includes("debt") ? "" : "")).join("").replace(/(<td style="width:90px[^>]*>)([^<]+)/g, (_m: string, a: string, b: string) => a + fmt(Number(String(b).replace(/,/g, ""))))}</table>`;
  const body = [
    section(`${metric("Average Tax Debt", "avg_debt", money)}${metric("HOT Records", "hot")}${metric("Absentee Owners", "absentee")}${metric("Probate / Heirs Count", "heirs_count")}${metric("Top Equity", "top_equity", money)}`),
    ctaSection("Reserve any of these counties — $149 launch price", "https://leadcurate.com/intake/"),
  ].join("");
  return shell("Market Comparison Audit", "Side by side", p.name, "Here is a side-by-side view of the counties you asked about.", body);
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
