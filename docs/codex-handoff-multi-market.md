# Codex Handoff — Multi-Market Support + Dashboard Buttons

> Read `/CLAUDE.md` §3 (5-tier pricing) and the new "TWO MODES of audit email" section first. This handoff extends `send-delivery` and `build_delivery.py` so we can sell beyond Wake NC.

---

## Status snapshot (verified 2026-06-30)

- ✅ `send-delivery` Edge Function v3 LIVE — supports `mode="delivery"` (XLSX attached, full data) and `mode="sample"` (redacted PII, bar charts, "Reserve Your County" CTA, no XLSX). Verified both modes hit Hostinger Mail 204.
- ✅ Branded audit HTML works in Gmail (Derrick's inbox confirmed). Uses table-based layout for cross-client compatibility.
- ✅ `build_delivery.py` script at `/opt/leadcurate/scripts/build_delivery.py` — hardcoded to Wake NC. Needs generalization.
- ✅ CLAUDE.md and Hermes skill (`/root/.hermes/skills/leadcurate/SKILL.md`) both updated with the two-mode flow.

---

## Task 1 — Generalize `build_delivery.py` for any market

**File:** `/opt/leadcurate/scripts/build_delivery.py`

Current state: hardcoded to read `/opt/leadcurate/raw_imports/wake-nc/2026-06-28/delinquent-latest.xlsx` and write `/tmp/Wake-NC-Curated-Distress-500.xlsx`.

**Required changes:**

1. Add CLI args via `argparse`:
   - `--market <slug>` (required) — e.g. `wake-nc`, `cobb-ga`, `harris-tx`
   - `--lane <lane>` (default `tax-delinquent`)
   - `--count <int>` (default 500)
   - `--output-dir <path>` (default `/tmp`)

2. Add a market registry at the top of the file:
   ```python
   MARKET_REGISTRY = {
     "wake-nc":      {"display": "Wake County NC", "raw_dir": "/opt/leadcurate/raw_imports/wake-nc", "raw_pattern": "delinquent-latest.xlsx", "default_city": "Raleigh", "state": "NC"},
     "cobb-ga":      {"display": "Cobb County GA", "raw_dir": "/opt/leadcurate/raw_imports/cobb-ga", "raw_pattern": "*.csv", "default_city": "Marietta", "state": "GA"},
     "guilford-nc":  {"display": "Guilford County NC", "raw_dir": "/opt/leadcurate/raw_imports/guilford-nc", "raw_pattern": "tax-delinquent-report.csv", "default_city": "Greensboro", "state": "NC"},
     "marion-in":    {"display": "Marion County IN", "raw_dir": "/opt/leadcurate/raw_imports/marion-in", ...},
     "dekalb-ga":    {...},
     "forsyth-nc":   {...},
     "fulton-ga":    {...},
     "harris-tx":    {...},
     "jefferson-al": {...},
   }
   ```

3. Auto-find the most recent date folder per market (sort `os.listdir(raw_dir)` by date suffix, pick newest).

4. Different raw schemas need different column mappings. Build a per-market parser plug-in:
   ```python
   def parse_wake_nc(row, H): ...  # current logic
   def parse_cobb_ga(row, H): ...  # different column names
   ```
   Dispatch based on `--market` arg.

5. Output filename: `{Market-Slug}-Curated-Distress-{count}.xlsx`

**Acceptance:**
- `python3 /opt/leadcurate/scripts/build_delivery.py --market wake-nc` produces the same output as today
- `python3 /opt/leadcurate/scripts/build_delivery.py --market guilford-nc` produces a valid XLSX from the Guilford raw file
- Both also write the matching preview JSON for the audit Edge Function

---

## Task 2 — Add `mode="comparison"` to send-delivery

**File:** `supabase/functions/send-delivery/index.ts` (modify in place; current is v3)

When a prospect is deciding which county to reserve, they want to compare 2–4 markets side-by-side.

**Payload shape for mode=comparison:**
```json
{
  "mode": "comparison",
  "to": "prospect@example.com",
  "name": "Jane Wholesaler",
  "markets": [
    {"slug":"wake-nc","name":"Wake NC","total":500,"hot":196,"absentee":156,"avg_debt":6490,"top_equity":4491937,"heirs_count":47,"median_years":2},
    {"slug":"cobb-ga","name":"Cobb GA","total":500,"hot":...},
    {"slug":"fulton-ga","name":"Fulton GA","total":500,"hot":...}
  ]
}
```

**Render side-by-side bar charts:**
- Bar chart: avg tax debt per market
- Bar chart: HOT records per market
- Bar chart: absentee owners per market
- Bar chart: probate (heirs) count per market
- Bar chart: top equity per market

Use the same `barRow` helper already in v3, but call it once per market for each metric.

**CTA at bottom:** `Reserve any of these counties — $149 launch price` linking to https://leadcurate.com/intake/

**No XLSX attached.** No sample records table (this email is purely comparative).

Design reference: `docs/property-numbers/index.html` — that's the "compare across markets" layout we're emulating.

---

## Task 3 — Dashboard buttons that fire send-delivery

**File:** `docs/command/index.html`

Two new buttons to add:

### 3a. "Send Sample Audit" button on intake/prospect cards
- Lives on the existing `intake:new` card next to "Review & Send Quote"
- Click → confirm dialog → POST to `https://jdmlsraqioigbukspduo.supabase.co/functions/v1/send-delivery` with `mode: "sample"` + payload built from the prospect's intake fields
- For analytics fields (debt_buckets, heirs_count, etc.) — use cached values from a recent build of that market, or call a small helper Edge Function `get-market-analytics?market=wake-nc` (build this if needed)

### 3b. "Send Delivery Audit" button on paid-customer cards
- Lives where the existing "Build quote link" is (or near it)
- Active only when customer status = paid
- Click → confirm → POST with `mode: "delivery"` + `list_url` set to the customer's specific XLSX URL
- Show inline "Sent" confirmation, refresh feed

### Acceptance test
- Fill out intake form with a real email
- See the `intake:new` card on dashboard
- Click **Send Sample Audit** → Sample Audit email arrives in test inbox with redacted records + bar charts
- Mark the same prospect as paid (manual SQL update for now)
- Click **Send Delivery Audit** → Delivery Audit with XLSX attached arrives
- Both events log to `activity_feed`

---

## Out of scope for this session

- ❌ `customer_deliveries` dedup table (track which parcels went to which customer) — future, after 3+ real customers
- ❌ DKIM/SPF/DMARC DNS records — separate Hostinger DNS task
- ❌ Payment integration — waiting on Derrick to pick Stripe/Mercury/Cash App
- ❌ Multi-lane scrape expansion (probate, code violations beyond what we have) — future
- ❌ Facebook/IG/X wiring — waiting on Derrick's Page token

---

## Acceptance for the whole batch

When Task 1 + 2 + 3 are done, post ONE row to `activity_feed`:
- `event_type: 'conf:done'`
- `source: 'codex'`
- `title: 'Multi-market support + comparison mode + dashboard buttons live'`
- `target: 'derrick'`

Then stop. Don't post chatter status updates while in progress.
