import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";
import type { SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

type MailPayload = Record<string, unknown>;

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function unauthorized(message = "Unauthorized") {
  return new Response(JSON.stringify({ error: message }), {
    status: 401,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function readString(payload: MailPayload, keys: string[]): string | null {
  for (const key of keys) {
    const value = payload[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return null;
}

function mailData(payload: MailPayload): MailPayload {
  const data = payload.data;
  return data && typeof data === "object" ? data as MailPayload : payload;
}

function extractFrom(payload: MailPayload): string | null {
  const direct = readString(payload, [
    "from",
    "from_addr",
    "fromAddress",
    "sender",
    "senderEmail",
    "email",
  ]);
  if (direct) return direct;

  const from = payload.from;
  if (from && typeof from === "object") {
    const nested = from as Record<string, unknown>;
    for (const key of ["email", "address", "value"]) {
      const value = nested[key];
      if (typeof value === "string" && value.trim()) return value.trim();
    }
  }

  return null;
}

function extractPreview(payload: MailPayload): string | null {
  const preview = readString(payload, [
    "preview",
    "snippet",
    "text",
    "bodyText",
    "body_text",
    "plainBody",
    "htmlBody",
    "message",
  ]);
  if (!preview) return null;
  return preview.length > 500 ? `${preview.slice(0, 497)}...` : preview;
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

async function loadHostingerWebhookSecret(supabase: SupabaseClient): Promise<string | null> {
  const { data, error } = await supabase.rpc("get_app_secret", {
    secret_name: "HOSTINGER_WEBHOOK_SECRET",
  });

  if (error) {
    console.error("Failed to load HOSTINGER_WEBHOOK_SECRET", error);
    return null;
  }

  return typeof data === "string" && data.trim() ? data.trim() : null;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return jsonResponse({ error: "Method not allowed" }, 405);

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const supabaseAdminKey = readSupabaseAdminKey();
  if (!supabaseUrl || !supabaseAdminKey) {
    return jsonResponse({ error: "Supabase admin env vars not configured" }, 500);
  }

  const supabase = createClient(supabaseUrl, supabaseAdminKey, {
    auth: { persistSession: false },
  });

  const expectedSecret = await loadHostingerWebhookSecret(supabase);
  if (!expectedSecret) return jsonResponse({ error: "HOSTINGER_WEBHOOK_SECRET not configured" }, 500);

  const auth = req.headers.get("authorization") ?? "";
  const expectedAuth = `Bearer ${expectedSecret}`;
  if (auth !== expectedAuth) return unauthorized();

  let payload: MailPayload;
  try {
    payload = await req.json();
  } catch (_error) {
    return jsonResponse({ error: "Invalid JSON payload" }, 400);
  }

  const message = mailData(payload);
  const fromAddr = extractFrom(message);
  if (!fromAddr) return jsonResponse({ error: "Missing sender address" }, 400);

  const subject = readString(message, ["subject", "title"]);
  const preview = extractPreview(message);

  const { data: emailRow, error: emailError } = await supabase
    .from("inbound_emails")
    .insert({
      from_addr: fromAddr,
      subject,
      preview,
      raw_payload: payload,
    })
    .select("id")
    .single();

  if (emailError) {
    console.error("inbound_emails insert failed", emailError);
    return jsonResponse({ error: "Failed to record inbound email" }, 500);
  }

  const activityTitle = `New email from ${fromAddr}`;
  const activityBody = subject
    ? `Subject: ${subject}${preview ? `\n\n${preview}` : ""}`
    : preview ?? "Inbound email received via Hostinger Agentic Mail webhook.";

  const { error: activityError } = await supabase.from("activity_feed").insert({
    event_type: "conf:status",
    source: "hostinger-mail",
    title: activityTitle,
    body: activityBody,
    target: "derrick",
  });

  if (activityError) {
    console.error("activity_feed insert failed", activityError);
    return jsonResponse({
      ok: true,
      inbound_email_id: emailRow.id,
      activity_warning: "Inbound email recorded, but activity feed insert failed.",
    });
  }

  return jsonResponse({ ok: true, inbound_email_id: emailRow.id });
});
