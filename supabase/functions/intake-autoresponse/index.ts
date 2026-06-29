type IntakeRecord = {
  id?: string;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  markets?: string[] | null;
  list_type?: string[] | null;
  urgency?: string | null;
  volume?: string | null;
  role?: string | null;
  notes?: string | null;
  source?: string | null;
  status?: string | null;
  created_at?: string | null;
};

const SB_URL = Deno.env.get("SUPABASE_URL") ?? "https://jdmlsraqioigbukspduo.supabase.co";
const SB_KEY =
  Deno.env.get("SUPABASE_PUBLISHABLE_KEY") ??
  Deno.env.get("SUPABASE_ANON_KEY") ??
  "sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4";
const FROM_EMAIL = Deno.env.get("LEADCURATE_FROM_EMAIL") ?? "LeadCurate <hello@leadcurate.com>";
const QUOTE_BASE_URL =
  Deno.env.get("LEADCURATE_QUOTE_BASE_URL") ?? "https://leadcurate.com/quote-template/";
const HOSTINGER_MAIL_BASE_URL =
  Deno.env.get("HOSTINGER_MAIL_BASE_URL") ?? "https://api.mail.hostinger.com";

const jsonHeaders = {
  "Content-Type": "application/json",
  "Connection": "keep-alive",
};

function normalize(value?: string | null): string {
  return String(value ?? "").trim().toLowerCase();
}

function firstMarket(record: IntakeRecord): string {
  const markets = Array.isArray(record.markets) ? record.markets.filter(Boolean) : [];
  return markets[0] || "your market";
}

function pickTier(record: IntakeRecord): { tierKey: string; label: string; reason: string } {
  const urgency = normalize(record.urgency);
  const role = normalize(record.role);
  const volume = normalize(record.volume);
  const notes = normalize(record.notes);

  if (
    (urgency.includes("need it now") || urgency.includes("24") || urgency.includes("48")) &&
    (urgency.includes("this week") || notes.includes("this week"))
  ) {
    return {
      tierKey: "hotsheet",
      label: "Tier 1 - Imminent Auction Hot Sheet",
      reason: "You flagged urgent timing and this-week need.",
    };
  }

  if (role.includes("acquisitions") && urgency.includes("this week")) {
    return {
      tierKey: "freshtrigger",
      label: "Tier 2 - Fresh Triggers Feed",
      reason: "An acquisitions team with this-week timing usually needs the newest trigger events first.",
    };
  }

  if (
    (volume.includes("500") || volume.includes("1500") || volume.includes("500-1500")) &&
    (role.includes("solo") || role.includes("individual"))
  ) {
    return {
      tierKey: "breakingpoint",
      label: "Tier 3 - The Breaking Point",
      reason: "Your solo operator profile and target volume point toward a tighter high-conversion subset.",
    };
  }

  return {
    tierKey: "deepdistress",
    label: "Tier 4 - Curated Distress List",
    reason:
      "This is the best starting lane when the intake does not point to an urgent or team-based trigger feed.",
  };
}

function buildQuoteUrl(record: IntakeRecord, tierKey: string): string {
  const params = new URLSearchParams();
  params.set("buyer", record.name || record.email || "LeadCurate prospect");
  params.set("market", firstMarket(record));
  params.set("tier", tierKey);
  return `${QUOTE_BASE_URL}?${params.toString()}`;
}

function emailBody(record: IntakeRecord, tier: { label: string; reason: string }, quoteUrl: string): string {
  const name = (record.name || "").trim();
  const greeting = name ? `Hi ${name},` : "Hi,";
  const market = firstMarket(record);
  return `${greeting}

Thanks for the inquiry. Based on what you shared, we recommend ${tier.label}.

Why: ${tier.reason}

Market: ${market}

Here is your personalized quote link:
${quoteUrl}

If you want a tighter slice, a different county, or a faster-turnaround option, just reply with the details and I'll point you to the right lane.

- Derrick
LeadCurate`;
}

function textToHtml(text: string): string {
  return text
    .split("\n\n")
    .map((paragraph) => `<p>${paragraph.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll("\n", "<br>")}</p>`)
    .join("\n");
}

function readSupabaseAdminKey(): string | null {
  const legacyServiceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacyServiceRoleKey) return legacyServiceRoleKey;

  const secretKeysJson = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (secretKeysJson) {
    try {
      const secretKeys = JSON.parse(secretKeysJson) as Record<string, string>;
      if (typeof secretKeys.default === "string" && secretKeys.default.trim()) {
        return secretKeys.default.trim();
      }
    } catch (_error) {
      console.error("SUPABASE_SECRET_KEYS is not valid JSON");
    }
  }

  return null;
}

async function loadSecret(name: string): Promise<string | null> {
  const adminKey = readSupabaseAdminKey();
  if (!adminKey) return null;

  const response = await fetch(`${SB_URL}/rest/v1/rpc/get_app_secret`, {
    method: "POST",
    headers: {
      apikey: adminKey,
      Authorization: `Bearer ${adminKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ secret_name: name }),
  });

  if (!response.ok) {
    console.error(`get_app_secret failed for ${name}`, response.status, await response.text());
    return null;
  }

  const data = await response.json();
  return typeof data === "string" && data.trim() ? data.trim() : null;
}

async function postActivity(event_type: string, title: string, body: string, target = "claude") {
  try {
    await fetch(`${SB_URL}/rest/v1/activity_feed`, {
      method: "POST",
      headers: {
        apikey: SB_KEY,
        Authorization: `Bearer ${SB_KEY}`,
        "Content-Type": "application/json",
        Prefer: "return=minimal",
      },
      body: JSON.stringify({ event_type, source: "intake-autoresponse", title, body, target }),
    });
  } catch (err) {
    console.error("activity_feed insert failed", err);
  }
}

async function sendWithHostinger(to: string, subject: string, text: string) {
  const token = await loadSecret("HOSTINGER_MAIL_TOKEN");
  let mailboxResourceId =
    (await loadSecret("HOSTINGER_MAILBOX_RESOURCE_ID")) ??
    Deno.env.get("HOSTINGER_MAILBOX_RESOURCE_ID");

  if (!token) {
    return { sent: false, provider: "hostinger", reason: "HOSTINGER_MAIL_TOKEN not configured" };
  }

  if (!mailboxResourceId) {
    mailboxResourceId = await discoverMailboxResourceId(token);
  }

  if (!mailboxResourceId) {
    return {
      sent: false,
      provider: "hostinger",
      reason: "Could not discover HOSTINGER_MAILBOX_RESOURCE_ID",
    };
  }

  const response = await fetch(
    `${HOSTINGER_MAIL_BASE_URL.replace(/\/$/, "")}/api/v1/mailboxes/${encodeURIComponent(mailboxResourceId)}/send`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        to: [to],
        displayName: FROM_EMAIL.replace(/^(.+?)\s*<.*>$/, "$1"),
        subject,
        text,
        html: textToHtml(text),
      }),
    },
  );

  const responseText = await response.text();
  if (response.status !== 204) {
    throw new Error(`Hostinger Mail ${response.status}: ${responseText}`);
  }

  return { sent: true, provider: "hostinger", response: "204 No Content" };
}

async function discoverMailboxResourceId(token: string): Promise<string | null> {
  const response = await fetch(`${HOSTINGER_MAIL_BASE_URL.replace(/\/$/, "")}/api/v1/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    console.error("Hostinger Mail /me failed", response.status, await response.text());
    return null;
  }

  const payload = await response.json();
  const mailboxes = Array.isArray(payload?.data?.mailboxes) ? payload.data.mailboxes : [];
  const preferredAddress = FROM_EMAIL.includes("<")
    ? FROM_EMAIL.split("<")[1].split(">")[0].trim().toLowerCase()
    : FROM_EMAIL.trim().toLowerCase();

  const preferred = mailboxes.find(
    (mailbox: any) => String(mailbox?.address ?? "").trim().toLowerCase() === preferredAddress,
  );
  const selected = preferred ?? (mailboxes.length === 1 ? mailboxes[0] : null);
  const resourceId = selected?.resourceId;

  return typeof resourceId === "string" && resourceId.trim() ? resourceId.trim() : null;
}

function extractRecord(payload: any): IntakeRecord | null {
  if (payload?.table && payload.table !== "intake_requests") return null;
  return payload?.record ?? payload?.new_record ?? payload?.new ?? payload?.data ?? payload ?? null;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: jsonHeaders });
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "POST required" }), { status: 405, headers: jsonHeaders });
  }

  try {
    const payload = await req.json();
    const record = extractRecord(payload);

    if (!record || typeof record !== "object") {
      return new Response(JSON.stringify({ error: "No intake record found" }), {
        status: 400,
        headers: jsonHeaders,
      });
    }

    const tier = pickTier(record);
    const quoteUrl = buildQuoteUrl(record, tier.tierKey);
    const to = String(record.email ?? "").trim();
    const subject = `LeadCurate recommendation: ${tier.label}`;
    const text = emailBody(record, tier, quoteUrl);

    let emailResult: any = { sent: false, provider: "hostinger", reason: "No email on intake record" };
    if (to) {
      emailResult = await sendWithHostinger(to, subject, text);
    }

    const statusTitle = emailResult.sent
      ? `Auto-reply sent: ${tier.label}`
      : `Auto-reply prepared: ${tier.label}`;
    const statusBody = [
      `Intake id: ${record.id ?? "-"}`,
      `Prospect: ${record.name ?? "-"} <${to || "no email"}>`,
      `Recommended tier: ${tier.label}`,
      `Quote URL: ${quoteUrl}`,
      `Email sent: ${emailResult.sent ? "yes" : "no"}`,
      emailResult.sent ? `Provider: ${emailResult.provider}` : `Reason: ${emailResult.reason ?? "not sent"}`,
    ].join("\n");

    await postActivity(emailResult.sent ? "conf:done" : "conf:status", statusTitle, statusBody, "claude");

    return new Response(JSON.stringify({ ok: true, tier, quoteUrl, email: emailResult }), {
      headers: jsonHeaders,
    });
  } catch (err) {
    console.error(err);
    await postActivity("conf:blocker", "Intake autoresponse failed", String(err?.message ?? err), "derrick");
    return new Response(JSON.stringify({ ok: false, error: String(err?.message ?? err) }), {
      status: 500,
      headers: jsonHeaders,
    });
  }
});
