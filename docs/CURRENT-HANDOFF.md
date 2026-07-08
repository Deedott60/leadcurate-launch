# Current Handoff — Single Source of Truth

> **This file replaces dated `codex-handoff-*.md` snapshots.** It gets edited in place, not recreated. Old dated files live in `docs/codex-handoff-archive/` for history only — don't read them for current priorities.
>
> **Codex:** this is the file `AGENTS.md` step 2 points you to. Read this AND `docs/AGENT-OPERATING-RULES.md` every session, before checking `activity_feed`.
> **Danny/Hermes:** this is the file `hermes-skill/leadcurate/SKILL.md` §8 points you to.
> **Claude (any session):** when you finish work or Derrick makes a decision, update this file in place — move completed items to "Recently closed," add new items to "Open now." Don't create a new dated file.

Last updated: 2026-07-08 by Codex

---

## Open now

2. **Regional comparison pulls.** Run Bradley County TN, Marion County TN, and Walker County GA through the SAME `process_verified_vacant.py` pipeline used for Hamilton TN (already multi-market capable via the `MARKETS` dict). This gives the Chattanooga audit page's "Regional comparison" section real numbers instead of an honest placeholder. Add each to `MARKETS` in the script, following the Hamilton TN config as the template.
3. **Auto-generate the send-delivery payload from `meta.json`.** Right now every email send is a hand-typed `curl` payload (Claude did this all session 2026-07-08). Build a small script (`scripts/leadcurate/build_email_payload.py` or similar) that reads a market's `meta.json` output and produces the exact JSON `send-delivery` expects (`mode`, `market`, `lane`, `total`, `absentee`, `median_land_value`, `sample` rows redacted correctly, `audit_url`). This is the actual fix for "repeatable and automated" — read `supabase/functions/send-delivery/index.ts` to see the exact payload shape it expects (`renderSample`/`renderDelivery`/`deriveNumbers`/`genericSampleTable`).
4. **Backfill `ownership_type` into already-pulled markets.** `process_verified_vacant.py` now computes `ownership_type` (individual/entity) for every NEW pull, but Mecklenburg, Guilford, Forsyth, and any other markets already pulled before 2026-07-08 don't have it in their existing output files. Re-run the processor for those markets to backfill (cheap — it's just a re-run, source files are already on disk).
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
