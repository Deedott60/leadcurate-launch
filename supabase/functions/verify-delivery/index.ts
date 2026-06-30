import * as XLSX from "https://esm.sh/xlsx@0.18.5";

const SB_URL = Deno.env.get("SUPABASE_URL") ?? "https://jdmlsraqioigbukspduo.supabase.co";
const SB_KEY = Deno.env.get("SUPABASE_PUBLISHABLE_KEY") ?? Deno.env.get("SUPABASE_ANON_KEY") ?? "sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4";

const headers = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

type Expected = {
  total: number;
  hot: number;
  warm?: number;
  absentee: number;
  top_equity: number;
  heirs_count?: number;
  lane?: string;
  market?: string;
  allow_entities?: boolean;
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers });
}

function text(value: unknown): string {
  return String(value ?? "").trim();
}

function num(value: unknown): number {
  const n = Number(text(value).replace(/[$,]/g, ""));
  return Number.isFinite(n) ? n : 0;
}

function isHot(row: Record<string, unknown>) {
  return num(row["Total Owed"]) >= 10000 || num(row["Years Behind"]) >= 3 || text(row["Motivation"]).toUpperCase() === "HOT";
}

function isAbsentee(row: Record<string, unknown>) {
  return ["YES", "Y", "TRUE"].includes(text(row["Absentee Owner"]).toUpperCase());
}

function isEntity(owner: string) {
  return /\b(LLC|INC|CORP|TRUST|TTC|COMPANY|PROPERTIES|INVESTMENTS|HOLDINGS|PARTNERS|CHURCH|CITY|COUNTY)\b/i.test(owner);
}

async function openRouterReview(rows: Record<string, unknown>[], expected: Expected, checks: Record<string, unknown>) {
  const token = Deno.env.get("OPENROUTER_API_KEY");
  if (!token) return { ok: true, skipped: "OPENROUTER_API_KEY not configured" };
  const prompt = `Review this customer delivery. Does anything look off: wrong-looking owner names, addresses that are not real streets, debt numbers that do not make sense, or audit stats that do not match? Respond only JSON {\"ok\": boolean, \"issues\": string[]}.\nExpected: ${JSON.stringify(expected)}\nChecks: ${JSON.stringify(checks)}\nSample: ${JSON.stringify(rows.slice(0, 20))}`;
  const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model: "anthropic/claude-sonnet-4.6", messages: [{ role: "user", content: prompt }], response_format: { type: "json_object" } }),
  });
  if (!res.ok) return { ok: true, skipped: `OpenRouter ${res.status}: ${await res.text()}` };
  const payload = await res.json();
  const content = payload?.choices?.[0]?.message?.content ?? "{}";
  try {
    return JSON.parse(content);
  } catch {
    return { ok: true, skipped: "LLM response was not JSON" };
  }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers });
  if (req.method !== "POST") return json({ ok: false, error: "POST required" }, 405);
  try {
    const payload = await req.json();
    const expected = payload.expected as Expected;
    if (!payload.list_url || !expected) return json({ ok: false, error: "list_url and expected are required" }, 400);
    const file = await fetch(payload.list_url);
    if (!file.ok) return json({ ok: false, error: `Could not fetch list_url: ${file.status}` }, 400);
    const data = new Uint8Array(await file.arrayBuffer());
    const workbook = XLSX.read(data, { type: "array" });
    const sheetName = workbook.SheetNames.includes("Records") ? "Records" : workbook.SheetNames[0];
    const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(workbook.Sheets[sheetName], { defval: "" });
    const required = ["Owner Name", "Property Address", "Total Owed", "Estimated Equity", "Motivation"];
    const columns = new Set(rows.length ? Object.keys(rows[0]) : []);
    const duplicateKeys = new Set<string>();
    const seen = new Set<string>();
    for (const row of rows) {
      const key = `${text(row["Parcel REID"])}|${text(row["Account ID"])}`;
      if (seen.has(key)) duplicateKeys.add(key);
      seen.add(key);
    }
    const checks = {
      total: rows.length,
      hot: rows.filter(isHot).length,
      absentee: rows.filter(isAbsentee).length,
      top_equity: Math.max(0, ...rows.map((r) => num(r["Estimated Equity"]))),
      heirs_count: rows.filter((r) => /\b(heirs|hrs)\b/i.test(text(r["Owner Name"]))).length,
      duplicate_count: duplicateKeys.size,
      entity_owner_count: rows.filter((r) => isEntity(text(r["Owner Name"]))).length,
      missing_columns: required.filter((c) => !columns.has(c)),
    };
    const failures: string[] = [];
    if (checks.total !== expected.total) failures.push(`row count ${checks.total} != expected ${expected.total}`);
    if (checks.hot !== expected.hot) failures.push(`HOT count ${checks.hot} != expected ${expected.hot}`);
    if (checks.absentee !== expected.absentee) failures.push(`absentee count ${checks.absentee} != expected ${expected.absentee}`);
    if (Math.abs(checks.top_equity - expected.top_equity) > 100) failures.push(`top equity ${checks.top_equity} != expected ${expected.top_equity}`);
    if (expected.heirs_count !== undefined && checks.heirs_count !== expected.heirs_count) failures.push(`heirs count ${checks.heirs_count} != expected ${expected.heirs_count}`);
    if (checks.duplicate_count) failures.push(`${checks.duplicate_count} duplicate parcel/account keys`);
    if (!expected.allow_entities && checks.entity_owner_count) failures.push(`${checks.entity_owner_count} entity owners found`);
    if (checks.missing_columns.length) failures.push(`missing columns: ${checks.missing_columns.join(", ")}`);
    let llm: unknown = { skipped: "not requested" };
    if (!failures.length && payload.llm_review) {
      llm = await openRouterReview(rows, expected, checks);
      if ((llm as any)?.ok === false) failures.push(...(((llm as any).issues ?? ["LLM review failed"]).map(String)));
    }
    return json({ ok: failures.length === 0, failures, checks, llm });
  } catch (err) {
    return json({ ok: false, error: String((err as Error)?.message ?? err) }, 500);
  }
});
