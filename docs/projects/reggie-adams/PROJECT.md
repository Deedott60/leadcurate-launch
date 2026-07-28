# Reggie Adams — White-Label Package (PROJECT SOURCE OF TRUTH)

**Customer:** Reggie Adams · `mrreggieadams@gmail.com` · The 3 CCC'S Consulting Firm LLC
**Status:** Invoice sent, NOT paid. Order `69110f8b-422a-4bb9-a422-57d29c274a72` = `pending_payment`, $1,000, Cash App, **zero payment rows** (re-verified 2026-07-28).
**Owner of decisions:** Derrick. Agents do not quote prices or promise scope.

> **THIS IS THE ONLY FILE.** Every agent (Claude, Codex, Danny/Hermes) reads it for all Reggie
> work — build state, market scope, data quality, tickets, commercial scope, and rules.
> Update in place. Do not create dated copies. **Do not spin off a second Reggie doc** — if it
> is about Reggie, it belongs in here as a section.
>
> Reggie state also appears in exactly two other places, both of which point back here:
> the **Reggie project page** in the OS (`docs/command/index.html`) and the **conference room**
> in that same OS. `docs/CURRENT-HANDOFF.md` stays the company-wide file, not the Reggie file.

---

## 1. Verified build state (checked live 2026-07-19, not assumed)

| Piece | State | Where |
|---|---|---|
| White-label site (multi-page) | **BUILT + LIVE** | `premier-demo.leadcurate.com` |
| Renames to client brand via one config file | **WORKS** | `config/client.config.ts` in `whitelabel-investor-site` repo |
| Property Decision Tool (full workspace) | **BUILT + LIVE** | `premier-demo.leadcurate.com/tool` |
| Tool: search, records, map, comps, CSV import, Flip/Rental/BRRRR/Wholesale, print report | **WORKS** | standalone Next app, systemd `premier-demo-tool`, port 3101 |
| Tool connected to REAL property database | **NOT BUILT** | needs VPS search API (see §4) |
| Customer login / private workspace | **NOT BUILT** | |
| Reggie-specific config, domain, branding | **NOT STARTED** | waiting on payment + his assets |

**Important repo note:** the built site lives in the **separate** `whitelabel-investor-site` repo
(GitHub `Deedott60/whitelabel-investor-site`), not in `leadcurate-launch`. Earlier handoff text
saying "no implementation has started" predates that build. Both are true at different times;
this table is current.

## 2. Market scope (Derrick's decision — ten markets is OUT)

Ten live markets does not fit disk, refresh labor, or the price. **Recommended package: four markets.**

| Market | Why | Data on VPS today |
|---|---|---|
| **Wayne County / Detroit MI** | His stated priority, already deep | ✅ 7 verified lanes, processed 2026-07-19 |
| **Mecklenburg NC (Charlotte)** | Largest NC metro county | ✅ processed 2026-07-19 |
| **Wake NC (Raleigh)** | Largest/2nd NC county | ⚠️ raw current (07-18), processed STALE (07-08) — rebuild required |
| **Guilford NC (Greensboro/High Point)** | 3rd largest NC | ⚠️ processed 07-08 — rebuild required |

Three of four already have raw data pulled. This is why four is realistic and ten is not.

**Disk reality (verified):** 96G volume, 72G used, **25G free**. Reggie's four markets land around
7-8G total. Fits. The disk pressure is from other work (Cook 15.6G, Massachusetts 6.9G,
Dallas 6.3G, Harris 5.0G raw). If space tightens, archive Harris raw first — it has no processed
output. Do not delete DeShawn market data while that deal is open.

## 2b. DATA QUALITY GATE — affects two of Reggie's four markets

Codex's pre-launch QA pass (2026-07-24 to 07-27) measured **owner-occupied contamination** in
absentee-derived lanes. This hits Reggie's package directly.

| Lane | Mecklenburg | Wayne | Notes |
|---|---|---|---|
| tired-landlords | **84.9% owner-occupied** | 34.1% | not sellable as-is |
| absentee-owners | **80.1%** | 12.8% | not sellable as-is |
| out-of-state-owners | 0.8% | 0.1% | **clean, sellable** |

**Root cause:** exact-string comparison of property vs mailing address when counties format them
differently (`14611 N C 73 HY` vs `14611 HIGHWAY 73`). Mecklenburg also duplicates the city+state
suffix. Out-of-state lanes compare mailing *state*, so they were never affected.

**Fix status:** the canonical implementation now lives in `scripts/leadcurate/lane_quality.py`
(address roles + institutional-owner detection) and `process_investor_lanes.py` uses it.
**The contaminated lanes have NOT been rebuilt or released.** They are HELD, not deleted.
Zero customers ever received a defective file.

**Mandatory before anything reaches Reggie:** `scripts/leadcurate/qa_lane_gate.py` must pass on the
exact files that would ship. Exit code 1 = not sellable, not deliverable. Report the measured
number ("Mecklenburg tired-landlords now 1.4% owner-occupied"), never "rebuilt."

**Locked run order for this job** (`docs/AGENT-OPERATING-RULES.md`): map source columns to explicit
roles → build deduped one-row-per-parcel lanes → run `qa_lane_gate.py` on the shipping files →
hold and repair any failure → cut through the canonical 19-column schema → release only on
Derrick's explicit approval.

**Meeting-safe framing:** out-of-state-owner lanes are clean in all four markets today. Tired-landlord
and absentee lanes need the rebuild + gate pass before they are promised or delivered.

## 3. Data distribution (how Reggie actually receives records)

**Phase 1 (launch, buildable now):** private workspace page per market + lane. Customer picks
market and lane, server builds the file on the VPS, browser receives a download link only.
Reuses `scripts/leadcurate/build_delivery.py` and `verify_delivery_bundle.py`. No county-sized
payload ever hits the browser.

**Phase 2 (live tool queries):** the tool already ships a server connector route
(`/api/connectors/search`) that reads `LEADCURATE_API_URL` + `LEADCURATE_API_KEY` server-side and
returns normalized records. **The client half is done.** What is missing is the LeadCurate search
API it points at. That is the single highest-value build item.

Category/lane selection per market gets locked with Derrick before any pull is called
customer-ready. Time-sensitive lanes (tax, foreclosure) must refresh before delivery.

## 4. Build order

**Codex (server/data lane):**
- **R-1** Build the VPS property search API the tool already expects: `GET /search` with
  `q`, `market`, `lane`, `limit`, `offset`; API-key auth; returns normalized JSON matching the
  tool's `PropertyRecord` shape (id, address, city, state, zip, apn, county, owner,
  propertyType, beds, baths, sqft, yearBuilt, lat, lng, askingPrice, arv, repairs, rent,
  soldPrice). Server-side pagination. Reads from existing processed lane files.
- **R-2** Rebuild **Wake NC** from newest official inputs (`raw_imports/wake-nc/2026-07-18/`)
  through `lane_quality.py`. Do not ship from the 07-08 processed folder. Gate must pass.
- **R-3** Rebuild **Guilford NC** from newest official source through `lane_quality.py`. Gate must pass.
- **R-2b** Rebuild **Mecklenburg + Wayne** absentee and tired-landlord lanes through
  `lane_quality.py` and pass `qa_lane_gate.py`. These are the contaminated lanes in §2b and are
  currently HELD. Out-of-state lanes in both markets are clean and need no rebuild.
- **R-4** Market/lane registry: one config listing Reggie's four markets, their available lanes,
  source dates, and refresh cadence, consumable by both the API and the workspace.
- **R-5** Export job endpoint: build file on VPS, return signed download link, log to `deliveries`.

**Claude (customer-facing lane):**
- **C-1 — DONE (prepared, not active) 2026-07-28.** Reggie client config staged in the
  `whitelabel-investor-site` repo at `config/clients/reggie-adams.config.ts`, with an activation
  checklist at `config/clients/README.md`. The file is **inert** — every route imports
  `@/config/client.config`, nothing imports `config/clients/`, so the live demo is untouched.
  No `wl_clients` row was created (unpaid); `clientId` is the sentinel `PENDING_WL_CLIENT_ROW`,
  which is not a valid UUID, so a premature deploy fails loudly instead of writing Reggie's
  leads against the demo client. Every unknown — brand name, domain, phone, logo, palette,
  territory, tool URL — is a `PENDING_*` marker, not a guess. Typechecks clean.
- **C-2** Private workspace shell: login, market/category picker, download center, tool embedded.
  **Not started.** Do not build the category picker until §5.3 is answered.
- **C-3 — DRAFTED 2026-07-28, NOT SENT.** Commercial scope now lives in **§5 of this file**.
  It is blocked on Derrick, not on Claude. **Derrick approves before any of it reaches Reggie.**
- **C-4 — DONE.** Reggie project page in the OS (`docs/command/index.html`), nav item + `#page-reggie`.

**Blocked until Derrick decides** (detail in §5): market count, which data categories Reggie gets,
additional-market pricing, monthly hosting/maintenance fee, included support hours, refresh
cadence, cancellation terms, IP/license wording.

## 5. Commercial scope (C-3) — DRAFT, NOT SENT, NOT APPROVED

> Derrick approves before any of this reaches Reggie. Every `[DERRICK: ___]` blank is a
> commercial decision **no agent may fill in** — not with a guess, not with a "typical" number,
> not with a number from another deal.

### 5.1 Reference facts (verified 2026-07-28, not assumed)

| Field | Value | Source |
|---|---|---|
| Entity | The 3 CCC'S Consulting Firm LLC | `orders.metadata.company` |
| Invoice | `LC-2026-0718-001`, issued 2026-07-18 | `orders.metadata` |
| Amount | $1,000.00 USD, `initial_project_payment` | `orders.amount_cents` = 100000 |
| Method | Cash App `$Derrick607` | `orders.metadata.cash_app` |
| Payment status | **`pending_payment` — unpaid, zero payment rows** | live check |
| Market field on invoice | "Detroit/Wayne MI + Wake NC" | `orders.market` |

The invoice states an amount, not a boundary. §5 is the boundary. Do not change or resend the
invoice (rule 2 in §6).

### 5.2 BLOCKER — market count contradiction

- The **invoice** (`orders.market`) says **Detroit/Wayne MI + Wake NC** — two markets.
- **§2 above** recommends **four**: Wayne MI, Mecklenburg NC, Wake NC, Guilford NC.

Both are in writing and they disagree. `[DERRICK: two / four]` — this cannot go out with both
readings alive.

### 5.3 BLOCKER — which data categories Reggie gets is NOT decided

Derrick has not negotiated this with Reggie. **No category is promised, listed, or implied to
him until that conversation happens.** `[DERRICK: categories included — ___ ]`

Internal supply-side facts to inform that decision — **not a menu to hand Reggie**:

- **Out-of-state owners** — measured clean (0.1%–0.8% owner-occupied). The one category we
  could stand behind today.
- **Tired landlords** — Derrick has said he likely will not offer this at all. Also HELD on
  quality (Mecklenburg 84.9% owner-occupied, Wayne 34.1%).
- **Absentee owners** — HELD on quality (Mecklenburg 80.1%, Wayne 12.8%).
- **Wake NC / Guilford NC** — processed output stale (2026-07-08); rebuild required before
  anything from those markets ships, whatever the category.

Whatever Derrick lands on, every file must pass `scripts/leadcurate/qa_lane_gate.py` on the
exact shipping file first. **Never** send Reggie a category list, an availability menu, or a
record count before Derrick has negotiated and approved it.

### 5.4 BLOCKER — no recurring fee is defined

$1,000 is logged as `initial_project_payment`. It does not cover ongoing hosting, data refresh,
or support. **If scope goes out silent on a recurring fee, silence becomes the deal.**

| Item | `[DERRICK: ___]` |
|---|---|
| Monthly hosting + maintenance | `$___ /mo` |
| Data refresh | `included / $___` |
| Included support | `___ hrs/mo`, then `$___ /hr` |
| Additional market | `$___ each` |
| Billing start | `on launch / ___ days after` |
| Refresh cadence | `___` (tax/foreclosure must refresh before delivery regardless) |

### 5.5 Phase 1 — what the build delivers

Branded website: dual-audience homepage, seller journey with lead capture (`/sell`), outreach
transparency and opt-out (`/why-contacted`), investor services intake (`/investors`), Deal
Analyzer (`/analyzer`), privacy/terms/sitemap/`robots.txt`/`llms.txt`/structured data,
server-side lead storage with confirmation email, scripted (non-AI) qualification chatbot.

Property Decision Tool: branded instance — search, records, map, comps, Flip/Rental/BRRRR/
Wholesale side by side, field notes, CSV import, printable decision report. **Ships with sample
data** (rule 4 in §6).

Market data: private workspace page per contracted market; file built server-side, browser gets
a download link only. Categories per §5.3.

Territory: the markets we can source **data** in are not the territory Reggie **markets** in.
City pages under his brand are a public claim about where he buys — he confirms in writing.

Revisions: `[DERRICK: ___]` rounds within the delivered page set.

Branding assets — logo, colors, phone, domain, territory, mailing address — **not yet received**.
Delivery timing runs from the later of payment and receipt of assets, not from the invoice date.

### 5.6 Explicitly NOT in Phase 1

Rule 3 in §6 forbids telling Reggie any of this is included or built.

- **Live property data inside the tool.** The tool's server connector is built and waiting; the
  search API it points at is **not built** (R-1). Until then the tool runs on sample data and
  market data ships as files. Phase 2, priced separately.
- **Customer login / self-service account area.** Not built. Access is provisioned by us.
- **Markets beyond the contracted set.** Priced per market (§5.4).
- **Leads, deals, closings, traffic, ranking, or revenue.** Nothing about outcomes is promised.
- **Skip tracing, phone/email append, dialer, CRM, outbound sending.** Not in scope, not built.
- **Custom feature development** outside the page set in §5.5.

### 5.7 Data license, ownership, term — `[DERRICK: approve wording]`

Proposed, none of it agreed:

- Data licensed to The 3 CCC'S Consulting Firm LLC for its own internal use. **No resale,
  redistribution, sublicensing, or bulk transfer.**
- Records derive from public county/municipal and licensed sources, provided as-is, accuracy not
  warranted; Reggie verifies independently and owns his own outreach compliance (TCPA, state
  calling/texting rules, DNC, CAN-SPAM) and opt-out handling.
- LeadCurate retains the platform, source code, and tooling. Reggie gets a **license to use** his
  instance, not ownership of the codebase. He owns his brand, domain, content, and captured leads.
- No exclusivity unless separately agreed. `[DERRICK: is any market exclusivity offered?]`
- Term `[DERRICK: month-to-month / ___ min]`, notice `[DERRICK: ___ days]`, initial payment
  `[DERRICK: non-refundable / ___]`. On cancellation Reggie keeps delivered files, domain, leads.

### 5.8 Acceptance

1. Derrick confirms funds in Cash App `$Derrick607`. **No agent marks an order paid.**
2. Reggie provides brand assets (§5.5).
3. We deploy his instance and give him access.
4. Reggie has `[DERRICK: ___ days]` to raise issues against §5.5; acceptance is automatic after.

### 5.9 How agents handle §5

1. Nothing in §5 reaches Reggie without Derrick's explicit approval, and it goes out through
   `send-delivery` (rule 7 in §6).
2. No agent fills a `[DERRICK: ___]` blank.
3. No agent softens §5.3 or §5.6. The undecided categories, the held lanes, and the unbuilt
   search API are what a friendly rewrite smooths away first. They survive every edit.
4. No record counts appear anywhere unless measured on the exact files that would ship.

---

## 6. Hard rules for this project

1. Do not mark the order paid until Derrick confirms money in Cash App `$Derrick607`.
2. Do not change or resend invoice `LC-2026-0718-001`.
3. Do not tell Reggie ten markets, live data, or the connected workspace are included/built.
4. Sample data stays in the tool until real market data is authorized and wired.
5. Newest official source per LOCKED rule; mark unsupported lanes unavailable, never infer.
6. No fabricated counts, testimonials, or track record anywhere customer-facing.
7. All customer email goes through `send-delivery` and to Derrick for review unless he says send.
