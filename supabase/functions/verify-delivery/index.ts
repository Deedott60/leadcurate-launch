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
  hot?: number;
  warm?: number;
  absentee?: number;
  top_equity?: number;
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

function firstColumn(columns: Set<string>, candidates: string[]) {
  return candidates.find((candidate) => columns.has(candidate)) ?? "";
}

function parseCsv(csv: string) {
  const parsed: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < csv.length; index += 1) {
    const char = csv[index];
    if (quoted) {
      if (char === '"' && csv[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      parsed.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field || row.length) {
    row.push(field.replace(/\r$/, ""));
    parsed.push(row);
  }
  const headers = parsed.shift() ?? [];
  return parsed.filter((values) => values.some(Boolean)).map((values) =>
    Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]))
  );
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
      if (file.ok) return { file, resolved_url: url };
      lastError = `${url}: ${file.status}`;
    } catch (err) {
      lastError = `${url}: ${String((err as Error)?.message ?? err)}`;
    }
  }
  throw new Error(`Could not fetch list_url: ${lastError}`);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers });
  if (req.method !== "POST") return json({ ok: false, error: "POST required" }, 405);
  try {
    const payload = await req.json();
    const expected = payload.expected as Expected;
    if (!payload.list_url || !expected) return json({ ok: false, error: "list_url and expected are required" }, 400);
    const { file, resolved_url } = await fetchDeliveryFile(String(payload.list_url));
    const data = new Uint8Array(await file.arrayBuffer());
    const legacyRequired = ["Owner Name", "Property Address", "Total Owed", "Estimated Equity", "Motivation"];
    let rows: Record<string, unknown>[] = [];
    let sheetName = "CSV";
    const isCsv = file.headers.get("content-type")?.includes("text/csv") || String(resolved_url).toLowerCase().split("?")[0].endsWith(".csv");
    if (isCsv) {
      rows = parseCsv(new TextDecoder().decode(data));
    } else {
      const workbook = XLSX.read(data, { type: "array" });
      sheetName = workbook.SheetNames[0];
      for (const candidate of workbook.SheetNames) {
        const candidateRows = XLSX.utils.sheet_to_json<Record<string, unknown>>(workbook.Sheets[candidate], { defval: "" });
        const candidateColumns = new Set(candidateRows.length ? Object.keys(candidateRows[0]) : []);
        const hasLegacyShape = legacyRequired.every((column) => candidateColumns.has(column));
        const hasPropertyShape = Boolean(
          firstColumn(candidateColumns, ["Owner Name", "owner_name"]) &&
          firstColumn(candidateColumns, ["Property Address", "property_address"]) &&
          firstColumn(candidateColumns, ["Parcel ID", "Parcel REID", "parcel_id"])
        );
        if (hasLegacyShape || hasPropertyShape) {
          sheetName = candidate;
          rows = candidateRows;
          break;
        }
      }
      if (!rows.length) {
        rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(workbook.Sheets[sheetName], { defval: "" });
      }
    }
    const columns = new Set(rows.length ? Object.keys(rows[0]) : []);
    const ownerColumn = firstColumn(columns, ["Owner Name", "owner_name"]);
    const addressColumn = firstColumn(columns, ["Property Address", "property_address"]);
    const parcelColumn = firstColumn(columns, ["Parcel ID", "Parcel REID", "parcel_id"]);
    const accountColumn = firstColumn(columns, ["Account ID", "account_id"]);
    const hotAvailable = ["Total Owed", "Years Behind", "Motivation"].some((column) => columns.has(column));
    const absenteeColumn = firstColumn(columns, ["Absentee Owner", "is_absentee_owner"]);
    const equityColumn = firstColumn(columns, ["Estimated Equity", "equity"]);
    const duplicateKeys = new Set<string>();
    const seen = new Set<string>();
    for (const row of rows) {
      const key = `${text(row[parcelColumn])}|${accountColumn ? text(row[accountColumn]) : ""}`;
      if (seen.has(key)) duplicateKeys.add(key);
      seen.add(key);
    }
    const checks = {
      total: rows.length,
      hot: hotAvailable ? rows.filter(isHot).length : null,
      absentee: absenteeColumn ? rows.filter((row) => isAbsentee({ "Absentee Owner": row[absenteeColumn] })).length : null,
      top_equity: equityColumn ? Math.max(0, ...rows.map((row) => num(row[equityColumn]))) : null,
      heirs_count: ownerColumn ? rows.filter((row) => /\b(heirs|hrs)\b/i.test(text(row[ownerColumn]))).length : null,
      duplicate_count: duplicateKeys.size,
      entity_owner_count: ownerColumn ? rows.filter((row) => isEntity(text(row[ownerColumn]))).length : 0,
      missing_columns: [
        ownerColumn ? "" : "Owner Name",
        addressColumn ? "" : "Property Address",
        parcelColumn ? "" : "Parcel ID",
      ].filter(Boolean),
      sheet_name: sheetName,
      resolved_url,
    };
    const failures: string[] = [];
    if (checks.total !== expected.total) failures.push(`row count ${checks.total} != expected ${expected.total}`);
    if (expected.hot !== undefined && checks.hot === null) failures.push("HOT metric requested but no HOT source columns were found");
    else if (expected.hot !== undefined && checks.hot !== expected.hot) failures.push(`HOT count ${checks.hot} != expected ${expected.hot}`);
    if (expected.absentee !== undefined && checks.absentee === null) failures.push("absentee metric requested but no absentee source column was found");
    else if (expected.absentee !== undefined && checks.absentee !== expected.absentee) failures.push(`absentee count ${checks.absentee} != expected ${expected.absentee}`);
    if (expected.top_equity !== undefined && checks.top_equity === null) failures.push("top equity requested but no equity source column was found");
    else if (expected.top_equity !== undefined && checks.top_equity !== null && Math.abs(checks.top_equity - expected.top_equity) > 100) failures.push(`top equity ${checks.top_equity} != expected ${expected.top_equity}`);
    if (expected.heirs_count !== undefined && checks.heirs_count === null) failures.push("heirs count requested but no owner source column was found");
    else if (expected.heirs_count !== undefined && checks.heirs_count !== expected.heirs_count) failures.push(`heirs count ${checks.heirs_count} != expected ${expected.heirs_count}`);
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
