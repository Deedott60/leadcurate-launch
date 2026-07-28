# Reggie Adams — White-Label Package (PROJECT SOURCE OF TRUTH)

**Customer:** Reggie Adams · `mrreggieadams@gmail.com` · The 3 CCC'S Consulting Firm LLC
**Status:** Invoice sent, NOT paid. Order `69110f8b-422a-4bb9-a422-57d29c274a72` = `pending_payment`, $1,000, Cash App, **zero payment rows** (verified 2026-07-19).
**Owner of decisions:** Derrick. Agents do not quote prices or promise scope.

> Every agent (Claude, Codex, Danny/Hermes) reads THIS file for Reggie work.
> `docs/CURRENT-HANDOFF.md` stays the company-wide file; this is the project file.
> Update in place. Do not create dated copies.

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
- **C-1** Reggie client config + branded site instance (name/domain/colors swap on payment).
- **C-2** Private workspace shell: login, market/lane picker, download center, tool embedded.
- **C-3** Written scope/addendum matching the invoice: Phase 1 four markets, expansion priced
  separately, recurring hosting/data fee, IP/license boundary. **Derrick approves before it goes out.**
- **C-4** Reggie project section in the OS (`docs/command/index.html`) so all four of us track state.

**Blocked until Derrick decides:** additional-market pricing, monthly hosting/maintenance fee,
included support hours, refresh cadence per lane, cancellation terms, IP/license wording.

## 5. Hard rules for this project

1. Do not mark the order paid until Derrick confirms money in Cash App `$Derrick607`.
2. Do not change or resend invoice `LC-2026-0718-001`.
3. Do not tell Reggie ten markets, live data, or the connected workspace are included/built.
4. Sample data stays in the tool until real market data is authorized and wired.
5. Newest official source per LOCKED rule; mark unsupported lanes unavailable, never infer.
6. No fabricated counts, testimonials, or track record anywhere customer-facing.
7. All customer email goes through `send-delivery` and to Derrick for review unless he says send.
