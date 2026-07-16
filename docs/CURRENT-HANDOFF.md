# Current Handoff — Single Source of Truth

> **This file replaces dated `codex-handoff-*.md` snapshots.** It gets edited in place, not recreated. Old dated files live in `docs/codex-handoff-archive/` for history only — don't read them for current priorities.
>
> **Codex:** this is the file `AGENTS.md` step 2 points you to. Read this AND `docs/AGENT-OPERATING-RULES.md` every session, before checking `activity_feed`.
> **Danny/Hermes:** this is the file `hermes-skill/leadcurate/SKILL.md` §8 points you to.
> **Claude (any session):** when you finish work or Derrick makes a decision, update this file in place — move completed items to "Recently closed," add new items to "Open now." Don't create a new dated file.

Last updated: 2026-07-15 by Codex (DeShawn full-territory positioning corrected)

---

## Recently closed -- DeShawn fulfillment

0. **All four DeShawn audit pages built and live (Claude 2026-07-15).** Cover page `docs/sample-deliveries/deshawn-territory-2026-07-15/` links the three market audits (`deshawn-massachusetts-...`, `deshawn-dallas-...`, `deshawn-cook-county-...`). Every stat traced to the verified meta.json files, math node-checked, zero em dashes, noindex, not on the public hub. MA page recommends Worcester County with Springfield as the value play, from the real rollup. Review email to Derrick next; NOTHING goes to the buyer without his explicit go. Codex resolved the preview leak on 2026-07-15: source owner, address, coordinate, parcel ID, PIN, and account columns are now redacted in all three markets' row-level preview CSVs; full paid files retain the identifiers needed for official verification.

0a. **DeShawn's private territory operating-system page built (Codex 2026-07-15).** `docs/sample-deliveries/deshawn-operating-system-2026-07-15/` is a separate noindex command center and does not alter Claude's four audit pages. It frames the product for an experienced operator as territory selection + official-source normalization + dedupe + differentiated signal crosses + campaign order + parcel verification + reusable refresh configs, not as three CSV lists. The interactive planner covers all three markets and all six requested lanes, shows unavailable event-source lanes honestly, and distinguishes private client logic from contractual geographic exclusivity. Verified in Playwright at 1440x1000 and 390x844; planner interaction passed. Customer positioning rule going forward: for experienced buyers, lead with the repeatable operating system and first campaign decision, then use the broad lane counts as proof. NOTHING goes to DeShawn without Derrick's explicit go.

0b. **DeShawn's sendable three-market intelligence brief built (Codex 2026-07-15).** `docs/sample-deliveries/deshawn-three-market-intelligence-2026-07-15/` is the single customer-facing audit link Derrick asked for. It gives no property list. It covers the three-market recommendation, exact lane counts, data freshness and history ranges, Dallas 2026 refresh requirement, Cook current-value limitation, supported versus local-source lanes, protected Verified Vacant Land outcome language, one-business-day supported-source refresh target, and the priority structure inside each territory. **Derrick corrected the positioning after first review:** DeShawn is not being sold a capped campaign or a limited number of records. The offer is the complete qualifying universe across every supported lane in the purchased territory. High-signal crosses prove LeadCurate's value in organizing the sheer volume; they do not define the size of the sale. The page now leads with 1,124,710 supported-lane qualifications before cross-lane consolidation and promises a one-row-per-parcel master territory file with every lane flag preserved and no artificial record cap. Claude's four audit pages remain unchanged. Verified with Playwright at 1440x1000 and 390x844, including anchor navigation and lower market sections; zero console errors/warnings and zero em/en dashes. Ready for Derrick to review and send; Codex did not email DeShawn.

1. **COMPLETE: DeShawn Bunch — live prospect, 3 new markets, 6 lanes (completed 2026-07-15).** Real warm buyer: experienced investor (20+ properties bought/sold, has a crew), hour-long phone call done, Derrick promised personalized territory audits. Contact: `dbunch@debonairelites.com` (in the `prospects` table, status `engaged`). Emails to him require Derrick's explicit go, review copy to Derrick first, always.

   **His exact ask (verbatim from his message):** markets are "Massachusetts, Chicago, Dallas Texas"; lanes are "all pre-foreclosures, tax lien, tired landlords who have held properties 10-20 minimum, distressed off-market industrial and multi family, out of state owners, vacant land."

   **Verified inventory (checked live on VPS 2026-07-10):**
   - **Dallas TX**: raw data EXISTS at `/opt/leadcurate/raw_imports/dallas-tx/2026-06-19/` (`parcel2025.zip` 104MB + `2025-real-property-cert-roll.zip` 123MB, per the DCAD URLs already in the playbook). NEVER processed — no `/opt/leadcurate/processed/dallas-tx/` exists. Start here, it's the fastest win.
   - **Chicago = Cook County IL**: nothing on the VPS. Fresh pull. Cook County has strong open-data infrastructure (county Socrata portal + Assessor datasets) — probe playbook Tier 2 first.
   - **Massachusetts — WE pick the market, that's the product (decided by Derrick 2026-07-10).** Do NOT wait on the buyer to name a metro. The play: pull the statewide MassGIS standardized parcel layer (Level 3, covers all 351 municipalities), then compute a per-county (and top-city) lane-density rollup so the data itself tells us the best Massachusetts market for HIS specific lanes. MassGIS standardized parcels typically carry owner name, owner mailing address, use code, assessed land/building/total values, and last-sale date/price — VERIFY the actual field names on pull, don't assume. The rollup Codex outputs (a ranking meta/CSV, per county and per major city):
     - absentee/out-of-state owner count (mail state != MA)
     - vacant land candidates (six-check where fields allow)
     - 10-20+ year tenure owner count (last-sale date)
     - industrial + multifamily parcel counts by use code, crossed with absentee/tenure as the distress proxy
     - median values per segment
     Claude turns that ranking into the "we analyzed the whole state and here's YOUR market" analysis on the audit page. This is the blow-him-away deliverable: nobody hands a wholesaler a 351-municipality scan. Pre-foreclosure and tax-title lanes in MA go through Registry of Deeds / Land Court and municipal tax-title processes; scope what's actually pullable per the chosen county AFTER the rollup picks the market, and state honestly in meta what isn't available statewide.

   **Per market, Codex builds (in this order):**
   1. Pull raw per playbook tiers. APPEND every working URL/method to `docs/playbooks/county-data-pull.md` before session end (hard rule).
   2. Process each of the 6 lanes that the source data can genuinely support. Lane mapping to existing tooling:
      - **Vacant land** → `process_verified_vacant.py` (register each market in the `MARKETS` dict, Hamilton TN config as template; six-check + ownership_type + years_owned already built in)
      - **Out-of-state owners** → absentee flag, same pattern as everywhere (mail_state != property state)
      - **Tax lien/delinquent** → standard tax-delinquent lane (Guilford/Wake pattern)
      - **Pre-foreclosure** → Jefferson KY pattern (court/docket filings) where the county exposes them
      - **Tired landlords (10-20+ yr hold)** → years_owned tenure filter on sale dates; this is a NEW lane cut but the tenure computation already exists in the vacant processor — generalize it, don't rebuild it
      - **Distressed off-market industrial + multifamily** → property-type/land-use-code filter (industrial + multifamily classes) crossed with distress signals (delinquency, code violations, absentee). NEW cut. If a source can't support it honestly, say so in meta rather than fabricating.
   3. For every lane that processes successfully: emit the standard triple (full CSV + preview CSV + meta.json) so the sellable list ships same-day when payment confirms.
   4. Report `conf:done` per market with file paths + record counts. Do NOT touch customer-facing audit pages or emails — Claude builds those from your meta.json outputs (email template v13 is LOCKED, see section below).

   **Deliverable format (Derrick locked 2026-07-10):** each of DeShawn's 3 markets gets its OWN full-depth audit page (Chattanooga pattern, no shortcuts on visuals), plus one personal cover page with his name linking the three — the email's single Open Full Audit button opens the cover page. Claude builds all four pages.

   **Data quality bar (Derrick, 2026-07-10 — applies to every output on this job):**
   - **Deduped**: one row per parcel, aggregated properly (quality contract, CLAUDE.md principle #9 — already locked, enforced here explicitly).
   - **Maximum fields**: pull every useful column the source exposes, not the minimum. The Shelby TN 79-column universal-key build is the precedent — owner, mailing, values, use codes, sale history, everything the county publishes. The pitch is "info most can't get," so the file has to actually carry it.
   - **Differentiated cuts**: the lane crosses are the moat — tenure x absentee, industrial/multifamily x distress, not just raw category dumps anyone can download.
   - **Reusable, not one-off**: every script written for this job gets a per-market config (MARKETS-dict pattern), so the next customer's markets run through the same pipeline with a config entry, not a rewrite. The MA statewide rollup script especially — that becomes a permanent product capability (state-level market selection), not a DeShawn special.
   - **Accurate and orderly**: stats in meta.json must be computed from the same file that ships. No hand-typed numbers anywhere.

   **Completion proof (Codex 2026-07-15):** Dallas canonical has 756,508 unique parcels and 140 source fields; supported lane counts are 42,092 tired landlords, 18,504 industrial/multifamily distress, 31,794 out-of-state owners, and 36,870 verified-vacant parcels. Massachusetts fetched 2,558,878 statewide rows and retained 2,558,583 unique parcels; supported lane counts are 436,244, 54,443, 115,764, and 60,876 respectively, with a 14-county and 351-municipality density rollup. Cook canonical has 1,863,530 current parcels and 309 source fields; supported lane counts are 84,780, 178,866, 61,559, and 2,918. All supported full files have zero duplicate parcels and file-matched metadata. Pre-foreclosure and tax-delinquent triples contain explicit source-limit reasons wherever current public data was unavailable. Outputs are under `/opt/leadcurate/processed/{dallas-tx,massachusetts-statewide,cook-il}/2026-07-15/`; source methods are in `docs/playbooks/county-data-pull.md`.

## Open now

2. **Regional comparison pulls - Walker GA blocker only.** Bradley County TN and Marion County TN are complete through the same `process_verified_vacant.py` pipeline. Walker County GA is not complete: official qPublic is Cloudflare-blocked from the VPS and the reachable public ArcGIS layer lacks land value, building value, appraisal value, building count, and vacant/improved status. Do not fabricate a Walker comparison number. Next valid paths are browser access to qPublic, a bulk assessor export, or a public-records request.
4. **Backfill `ownership_type` - Forsyth NC blocker only.** Mecklenburg, Wake, Guilford, Fulton, and Marion IN have been rerun and now include `ownership_type`. Forsyth NC is not rerun because the current `parcels-hosted.csv` source has total value and improvement signals but does not expose separate land value and building/improvement value fields required by the six-check verified-vacant processor. Do not force it through by fabricating land/building values; find a better Forsyth parcel/value source first.
5. **Geocoding (bigger lift, scope it before starting).** This is the real fix for "geographic destiny" / heat maps — right now geography is municipality-level only, no real lat/long. The US Census Bureau has a free batch geocoder API (no cost, no key needed for reasonable volume) that could turn property addresses into coordinates, enabling real zip-level concentration and an honest density visualization instead of fake precision. Don't start this without confirming with Derrick first — it's a real build, not a quick add, and its own item in `AGENT-OPERATING-RULES.md`-style scoping should happen before code.
6. **n8n contractor outreach workflow — verify it actually works.** Files exist and are committed (`docs/n8n-workflows/nyc_contractor_outreach_manual.json`, `scripts/leadcurate/nyc_contractor_outreach_seed.py`, the `contractor_outreach_queue` migration), but nobody has confirmed end-to-end that the workflow actually sends through Hostinger correctly. Codex: test it for real (manual trigger only, per the locked rule — do not auto-activate), report `conf:done` with proof.

## Email template — LOCKED, read before touching send-delivery

`supabase/functions/send-delivery/index.ts` is the ONLY email-sending code for LeadCurate, now at v13 (deployed 2026-07-08). Major rebuild happened today:
- One generic renderer for every lane (`renderSample`/`renderDelivery`), content varies by data (`deriveNumbers`, `extraColumns`), never by a second code path.
- Table now shows up to 3 numeric columns dynamically (Owed+Equity+Yrs for debt lanes, Land Value+Acreage for vacant land), with HOT/WARM/VACANT status pills and an Absentee badge, matching the originally-proven Wake County design.
- Signs as **"The LeadCurate Team"**, never a personal name — decided 2026-07-08 so automated sends (Codex/Danny/workflows) don't attach Derrick's name to interactions he didn't personally have.
- **Zero em dashes anywhere in customer-facing copy.** Grep for `—` before calling any customer-facing text done. This is a hard rule now, see `AGENT-OPERATING-RULES.md`.
- If a new lane needs a field type the table doesn't handle, extend `extraColumns()`/`deriveNumbers()`. Do NOT write a new render function.

## Vacant Land audit page — the reusable pattern

`docs/sample-deliveries/chattanooga-verified-vacant-2026-07-08/index.html` is the reference template for every future county's Verified Vacant Land audit page. Sections, in order: Executive Summary → hero/Priority tier → How to work this list (call order) → differentiation vs. stale lists → six-factor verification (outcome language only) → Ownership Intelligence → Value bands → Market Intelligence (median vs. average skew called out explicitly) → Geography → Parcel size → Quality Summary checklist → Executive Insights (analyst-voice observations tied to real numbers) → Executive Recommendations → Nearby markets → What's in your file → Source. Every number on it is pulled from the real `meta.json` / production CSV, nothing estimated. When building the next county's page, copy this structure, swap the data, do NOT invent stats you can't back with a real computation — if something isn't available (years-owned, regional comparison), say so on the page instead of guessing.

## Payment status (do not re-litigate — this is done)

Both rails deployed and tested (Codex, 2026-07-07): `orders` + `payments` tables live, `payment-confirmation` Edge Function v1 deployed with token auth. Manual Cash App/Zelle and Stripe Payment Link both write the same order/payment record. **Only Derrick's provider pick is outstanding** — do not rebuild this.

## Soft-open pricing (locked 2026-07-07, do not re-litigate)

Tier 1 Hot Sheet $497 · Tier 2 Fresh Triggers $199/mo · Tier 3 Breaking Point $249 · Tier 4 Curated Distress $149 ($99 first 5 via `?price=99` on the quote template) · Tier 5 Ground Floor $299/report · Verified Vacant $149/county · Contractor cut $199 borough+class / $349 citywide · Asset Locator $750/file / $1,500 custom book. Baked into `docs/tiers/index.html` and `docs/quote-template/index.html`. **NOT on the public landing page** — quoted-with-preview + waitlist only, until Derrick's final confirm.

## Recently closed (for context, not action)

- **Bradley TN and Marion TN regional comparison pulls complete (Codex 2026-07-08).** Added `scripts/leadcurate/pull_tpad_land.py`, registered `bradley-tn` and `marion-tn` in `scripts/leadcurate/process_verified_vacant.py`, pulled official Tennessee Comptroller TPAD land-class parcels, and processed both through the same verified-vacant six-check pipeline. VPS verified output: Bradley 2,603 source rows, 33 verified-vacant candidates; Marion 2,306 source rows, 238 verified-vacant candidates.
- **send-delivery payload builder complete (Codex 2026-07-08).** Added `scripts/leadcurate/build_email_payload.py`, which reads a processed `meta.json`, chooses preview CSV for sample mode and full CSV for delivery mode, redacts owner/address sample rows for sample mode, and emits JSON matching `send-delivery` (`mode`, `market`, `lane`, `total`, `absentee`, `median_land_value`, `sample`, `audit_url`, optional `list_url`).
- **ownership_type backfill complete for configured markets (Codex 2026-07-08).** Reran `process_verified_vacant.py` on the VPS for Mecklenburg NC, Wake NC, Guilford NC, Fulton GA, and Marion IN. Verified each output CSV header includes `ownership_type` at column 13.
- **Years-owned enrichment for verified-vacant-land complete (Codex 2026-07-08).** `scripts/leadcurate/process_verified_vacant.py` now parses sale dates, computes `years_owned`, includes it in full/preview CSV output, and writes average/median ownership tenure to meta when sale dates are available.
- **Scraping playbook backfill complete (Codex 2026-07-08).** `docs/playbooks/county-data-pull.md` now documents York SC, Cabarrus NC, Lancaster SC, Gaston NC, Duval FL, Davidson TN, Tarrant TX, Maricopa AZ, Jefferson KY code-violations, Shelby TN, and Hamilton TN. The old undocumented-county placeholders are removed.
- **Hamilton County TN (Chattanooga) fully done, Derrick-approved 2026-07-08.** Real data pulled and verified (21,654 qualified parcels of 168,952 reviewed), full executive-analytics audit page built, ownership_type wired into the real pipeline, live at the URL above. Ready to send to the real Facebook lead (Jerome, `Jeromedoesdeals@gmail.com`) whenever Derrick gives the go.
- Scraping playbooks moved from a local-only Claude Code skill folder (unreachable by Codex/Danny) into the git repo at `docs/playbooks/` — this was the real root cause of counties getting re-solved from scratch.
- `AGENT-OPERATING-RULES.md` now has: Sync discipline, Vacant Land differentiation doctrine, Customer-facing writing style (em dash ban + signature rule), Email template discipline, Scraping/data-pull playbook discipline.
- Dead auction cron (Mecklenburg/Fulton/Wake, 0-row silent failure) disabled by Codex 2026-07-07.
- Asset Locator generalized (`scripts/leadcurate/asset_locator.py`), tested on Mecklenburg.
- NYC DOB cut tool got `--borough`/`--class` flags, tested on Brooklyn facade.
- Annual billing toggle hidden on landing page (both `site/index.html` and live `docs/site/index.html`).
- 4 new NC/SC markets (Gastonia, Concord, Rock Hill, Lancaster) added to intake form + property-numbers audit.

## Pending on Derrick only

- Payment provider pick (Stripe live vs. manual Cash App/Zelle).
- **Send the Jerome email** — reviewed and approved 2026-07-08, ready to go to `Jeromedoesdeals@gmail.com` whenever Derrick says send.
- Send outreach scripts (land groups → NYC facade contractors → Charlotte collection attorneys).
- ~1hr attorney review before first law-firm (Asset Locator) sale.
- Ground Floor pricing lock, ad carousel pick, Private Market Engine strategy review.
- **Geocoding go/no-go** (item 5 above) — real build, needs Derrick's sign-off before Codex starts.
