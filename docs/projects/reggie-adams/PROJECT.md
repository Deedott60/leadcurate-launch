# Reggie Adams — White-Label Package (PROJECT SOURCE OF TRUTH)

**Customer:** Reggie Adams · `mrreggieadams@gmail.com` · The 3 CCC'S Consulting Firm LLC
**Status:** **The $1,000 invoice `LC-2026-0718-001` is DEAD** (Derrick, 2026-07-28). It is not the
commercial basis for this project. Terms have not been agreed. Order row
`69110f8b-422a-4bb9-a422-57d29c274a72` still reads `pending_payment` in the DB and needs to be
voided/closed on Derrick's instruction — **no agent changes that row on its own.**
**Payment:** LeadCurate has its own Cash App. `[DERRICK: LeadCurate Cash App tag = ___ ]` — use
that, not a personal tag. No agent fills this in from an old record.
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

## 2. Market scope — **UNKNOWN. NOT DECIDED.**

**Derrick has not asked Reggie which markets he wants.** Until that conversation happens there is
no market list for this project. Not two, not four, not ten.

Everything below is **supply-side capability only** — what we could serve if asked. It is not a
package, not a recommendation to act on, and not a menu for Reggie. Ten live markets does not fit
disk or refresh labor, so ten is out as a matter of capacity; that is the only settled fact here.

`[DERRICK: markets Reggie actually wants = ___ ]`

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
- **C-4 — DONE, REPLACED BY RG-1/RG-2.** Reggie now lives in the Supabase-backed Projects
  workspace in the OS (`docs/command/index.html`). The old hardcoded invoice-first view is hidden;
  current project state comes from the project tables.

**Blocked until Derrick decides** (detail in §5): market count, which data categories Reggie gets,
additional-market pricing, monthly hosting/maintenance fee, included support hours, refresh
cadence, cancellation terms, IP/license wording.

## 5. Commercial scope (C-3) — DRAFT, NOT SENT, NOT APPROVED

> Derrick approves before any of this reaches Reggie. Every `[DERRICK: ___]` blank is a
> commercial decision **no agent may fill in** — not with a guess, not with a "typical" number,
> not with a number from another deal.

### 5.1 There is no live commercial basis right now

The $1,000 invoice is **dead**. Nothing has replaced it. There is no agreed price, no agreed
scope, no agreed market list, and no agreed terms with Reggie.

Historical record only, so nobody resurrects it by accident: order
`69110f8b-422a-4bb9-a422-57d29c274a72`, invoice `LC-2026-0718-001` issued 2026-07-18,
$1,000 `initial_project_payment`, market field "Detroit/Wayne MI + Wake NC". **All of it is
superseded.** Do not quote, resend, or build against any of it.

`[DERRICK: new commercial basis = ___ ]`

### 5.2 What the new deal is — `[DERRICK: ___ ]`

Price, structure (one-time / monthly / both), and what triggers start of work are all open.
No agent proposes a number.

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

1. **The $1,000 invoice is dead.** Do not quote it, resend it, revive it, or build against it.
   Payment, when there is one, goes to the **LeadCurate** Cash App (§ header blank), not a
   personal tag. No agent marks anything paid.
2. **No market list exists.** Never state, imply, or configure a market for Reggie until Derrick
   says which ones he asked for.
3. Do not tell Reggie ten markets, live data, or the connected workspace are included/built.
4. Sample data stays in the tool until real market data is authorized and wired.
5. Newest official source per LOCKED rule; mark unsupported lanes unavailable, never infer.
6. No fabricated counts, testimonials, or track record anywhere customer-facing.
7. All customer email goes through `send-delivery` and to Derrick for review unless he says send.

---

## 7. WORK ORDER FOR CODEX — make this project area real

Derrick's requirement, in his words: *"I need to be able to manage his entire project."* The
current Reggie page in the OS is **hardcoded HTML that Claude hand-edits.** That is the bug.
The OS is a live Supabase-backed app; the Reggie area must be too.

### RG-1 — Project tables (do this first)

The OS already talks to Supabase directly (`docs/command/index.html`, anon key + `createClient`,
tables `prospects`, `intake_requests`, `messages`, `activity_feed`, `scout_prospects`). Add
project tables in the same style:

- `projects` — id, name, client_name, client_entity, client_email, status, commercial_basis
  (nullable — Reggie's is currently NULL because the invoice is dead), notes, created_at
- `project_markets` — project_id, market, categories (nullable), status, source_date, notes.
  **Starts EMPTY for Reggie.** Derrick adds rows as he learns what Reggie wants. Nothing seeds it.
- `project_items` — project_id, kind (task | decision | blocker | deliverable), title, detail,
  owner (derrick | claude | codex | hermes), status, created_at
- `project_assets` — project_id, kind (landing_page | domain | logo | config | tool_instance),
  label, url, status

RLS consistent with the existing tables. Do not touch `001_wl_tables.sql`.

### RG-2 — Replace the static Reggie page with a data-driven project view

Same page slot (`#page-reggie`, nav `data-page="reggie"`), but every card reads from RG-1 and is
**editable in the browser**: Derrick adds a market, flips a decision, marks a deliverable done,
attaches the landing-page URL — no code edit, no agent. Generalize it as a Projects area that
renders any row in `projects`, with Reggie as the first one, so the next client is a row and not
another hand-written page.

Must be manageable from the page: add/remove markets, add/edit categories per market, record a
decision and who made it, attach assets (landing page, domain, logo, tool instance), post a
status update that also lands in the conference room.

### RG-3 — Landing page slot

Reggie's landing page belongs **inside his project area**, as a `project_assets` row of kind
`landing_page`, not as a hardcoded link. It stays empty until Derrick supplies the business name
and terms are agreed. The staged config
(`whitelabel-investor-site` → `config/clients/reggie-adams.config.ts`) is the thing that gets
activated and pointed at from that slot.

### RG-4 — Universal source/scraping rules (NOT Reggie-specific) — **PRIORITY**

Derrick's call, 2026-07-28: **do this properly, it protects every market and every client, not
just Reggie.** The contamination bug was not a Mecklenburg bug — it was a rule that only existed
inside one script. Any new county we add today can reintroduce it.

**Root cause to design against:** owner-occupancy was decided by *exact string comparison* of
property address vs mailing address. Counties format the same address differently
(`14611 N C 73 HY` vs `14611 HIGHWAY 73`), and Mecklenburg duplicates the city+state suffix. Result:
84.9% owner-occupied inside a "tired landlords" lane. Out-of-state lanes were unaffected only
because they compare mailing *state*, which is format-insensitive by luck, not by design.

**Deliverable: a market-agnostic section in `docs/AGENT-OPERATING-RULES.md`** — the company-wide
file, not this one — that every county inherits automatically:

1. **Explicit column-role mapping.** Every source column maps to a declared role
   (property_address, mailing_address, owner_name, mailing_state, …). No positional guessing, no
   fuzzy header matching. An unmapped required role = the market is not processable, and it is
   marked unavailable rather than inferred.
2. **Address normalization is mandatory before any comparison.** Directionals, street-type
   abbreviations, highway forms, punctuation, casing, and duplicated city/state suffixes all
   normalize first. No lane may compare raw address strings, ever.
3. **Institutional-owner detection** as a shared rule, not a per-script regex.
4. **Occupancy is derived, never assumed**, and derived only through the canonical helper in
   `scripts/leadcurate/lane_quality.py`. Any script that re-implements it is a defect.
5. **`qa_lane_gate.py` runs on the exact shipping files.** Exit 1 = not sellable, not deliverable.
   State the pass/fail threshold explicitly in the rules so it is not a judgment call.
6. **New-market onboarding checklist** every county must pass before its data can be sold:
   roles mapped → normalization applied → deduped one row per parcel → gate passed → lane marked
   available. A market that has not cleared the checklist is **unavailable**, not "probably fine."
7. **Regression fixtures.** Extend `test_lane_quality.py` with a fixture per known county format
   quirk (the NC highway form and the Mecklenburg duplicated suffix at minimum), so a future
   refactor cannot silently undo this.

**Report the measured number** ("Mecklenburg tired-landlords now 1.4% owner-occupied"), never the
word "rebuilt" on its own. Held lanes stay held until the gate passes and Derrick approves release.

### RG-5 — The project area is a COMMUNICATION surface, not a record

This is how Derrick keeps all of us connected. When he points Claude, Codex, or Hermes at the
Reggie project area, that agent must be able to get fully caught up **from the page alone** —
current state, open decisions, who owns what, what changed since last time, and what was said.

- Wire `project_items` and project status updates into the **conference room** both ways: a
  message can be filed against a project, and a project update shows in the conference log.
- Every agent reports Reggie progress **into the project area**, not into a chat that Derrick has
  to relay. If it only exists in one agent's session, it does not exist.
- Show last-updated and by-whom on each item, so Derrick can see instantly whether Claude and
  Codex are on the same page — the exact failure that prompted this work order.

### Infrastructure constraints — verified 2026-07-28, read before building

- **Supabase org `jrjtcapsqdfvnldhwyum` is on the FREE plan.** Free allows 2 active projects and
  we are at the cap: `Dashboard/Form LeadCurate` (ACTIVE) and `rooted` (ACTIVE), with
  `business-understanding-system` already INACTIVE. **Creating a new Supabase project per client
  is not free and would force a paid plan.** Do not do it.
- **White-label is multi-tenant by design.** `wl_clients` and `wl_seller_leads` already exist with
  a client id. Every new client is a ROW, not a new database. Same pattern applies to the RG-1
  project tables — `projects` holds many clients, Reggie is one row.
- `supabase/migrations/001_wl_tables.sql` in the whitelabel repo is **read-only** (their AGENTS.md
  rule 5). Do not modify or reapply it.
- **Delivery email is Hostinger Agentic Mail**, via `scripts/leadcurate/send_dollar_delivery.py`
  (`api.mail.hostinger.com`, creds in `/opt/leadcurate/.env`). **n8n is NOT wired for delivery** —
  it is a placeholder card on the Workflow page. Resend is only the white-label site's own
  lead-confirmation email. Do not assume any of these three are interchangeable.
- **Never send a county-sized file through the browser or as an email attachment.** Build on the
  VPS, return a signed download link (R-5). `build_delivery.py` and `verify_delivery_bundle.py`
  already exist — reuse, do not rewrite.

### Rules for Codex on this work order

- **Do not seed any market for Reggie.** `project_markets` starts empty. §2 is unknown.
- **Do not create or revive an invoice, price, or order row.** §5.1 — the $1,000 is dead.
- Read §6 before touching anything customer-facing.
- Report progress in the conference room, and update this file in place. **Do not create a second
  Reggie document.**

---

### Implementation status — 2026-07-28

| Item | Status | Verified result |
|---|---|---|
| **RG-1** | **DONE** | Four multi-client project tables are live in Supabase. Reggie is one `planning` project row with NULL commercial basis, zero approved markets, six tracked items, and three assets. Historical order `69110f8b-422a-4bb9-a422-57d29c274a72` remains `pending_payment` and was not changed. |
| **RG-2** | **DONE** | OS Projects view reads from Supabase and supports browser editing for projects, work items, markets, categories, assets, and statuses. Desktop and 390px phone layouts verified. |
| **RG-3** | **DONE / WAITING ON REGGIE** | `Reggie landing page` is a `project_assets` row with no URL and status `waiting`. Nothing was invented or activated. |
| **RG-4** | **DONE** | Universal exact-role mapping, shared occupancy derivation, institutional-owner detection, mandatory normalization, gate thresholds, and new-market checklist are locked in `docs/AGENT-OPERATING-RULES.md`; regression tests pass. Held market files remain held until separately rebuilt and measured. |
| **RG-5** | **DONE** | Conference Room messages can be filed under a project; project changes and project status posts appear in both the project Activity tab and Conference Room with agent attribution and timestamps. |

**Operating location:** LeadCurate OS → **Projects** → **Reggie Adams project**. This file remains
the detailed source of truth; the OS is the live management and communication surface.

---

## 8. WHAT WE NEED FROM REGGIE (Derrick's conversation checklist)

Nothing here is a price or a promise. It is the intake list — what we physically cannot build
without. Safe to ask for in any conversation, before or after terms.

### Must have before anything can be branded

| Ask | Why we need it | Blocked without it |
|---|---|---|
| **Business name as it should appear publicly** | Entity on file is The 3 CCC'S Consulting Firm LLC; that may not be his brand | Every headline, email, and legal page |
| **Logo** (SVG or high-res PNG) | Replaces `public/logo.svg` | Site looks unbranded |
| **Brand colors** (or approval to pick) | Config `colors` block | Site ships in neutral defaults |
| **Business phone** as it should display | Header, footer, schema | Contact paths |
| **Business mailing address** | **Legally required** in email footers (CAN-SPAM) | Cannot send a single email |

### Domain and email — the part that trips people up

**Yes — if it is his website on his domain, the email is set up on his domain, and you need
access to do it.** Ask for one of two things, his choice:

- **Option A (easier for us):** he adds us to his domain registrar/DNS, or gives us the records to
  publish. We handle it.
- **Option B (he keeps control):** we send him the exact DNS records and he pastes them in.

Either way we need **DNS access or a cooperative person on the other end**, because:

1. **The domain itself** must point at his site.
2. **Sending email as his brand** requires **SPF and DKIM records on his domain**. Without them,
   his confirmation emails land in spam and the site looks broken. This is not optional and it is
   the single most common launch delay.
3. **Where leads get delivered** — the inbox he actually reads. Can be his existing Gmail; that is
   a forwarding target, not a sending identity. **Sending as his domain and receiving at Gmail are
   two different things** — do not let the conversation blur them.

Ask him plainly: *"Do you already own the domain, and can you get into where it's managed?"* If he
does not own one yet, that is a decision, not a blocker — it just has to happen before launch.

### Needed before any data work

| Ask | Note |
|---|---|
| **Which markets/territories he wants** | §2 — nobody has asked him. This is the open question. |
| **What he does with the records** | Drives which categories fit. Do not offer a menu (§5.3). |
| **How he wants records delivered** | Download link is what we build; confirm it works for him. |

### Not needed from him

Do not ask for anything payment-related beyond what terms require. **No agent asks Reggie for
money, card details, or account access.** Payment conversation is Derrick's alone.
