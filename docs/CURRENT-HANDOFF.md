# Current Handoff — Single Source of Truth

> **This file replaces dated `codex-handoff-*.md` snapshots.** It gets edited in place, not recreated. Old dated files live in `docs/codex-handoff-archive/` for history only — don't read them for current priorities.
>
> **Codex:** this is the file `AGENTS.md` step 2 points you to. Read this AND `docs/AGENT-OPERATING-RULES.md` every session, before checking `activity_feed`.
> **Danny/Hermes:** this is the file `hermes-skill/leadcurate/SKILL.md` §8 points you to.
> **Claude (any session):** when you finish work or Derrick makes a decision, update this file in place — move completed items to "Recently closed," add new items to "Open now." Don't create a new dated file.

Last updated: 2026-07-08 by Claude (Sonnet 5)

---

## Open now

1. **Hamilton County TN (Chattanooga) pull — real buyer waiting.** Facebook lead Jerome (`Jeromedoesdeals@gmail.com`) wants vacant land in Hamilton County. Pull the parcel file, run through `process_verified_vacant.py` (six-check process, absentee-flagged), then build a **customer-facing** audit (NOT the internal `property-numbers.html` methodology style — outcome language only, never list the six checks or scoring logic, per the Vacant Land differentiation doctrine in `AGENT-OPERATING-RULES.md`). Add a short "nearby markets worth a look" teaser (Bradley TN, Marion TN, Sequatchie TN, Walker GA, Catoosa GA — verify these are the real neighbors before naming any). Add Chattanooga TN to the intake form + property-numbers audit list once the pull is real. Report `conf:done` with file path + record counts.
2. **Executive-report delivery email** — in progress, uncommitted local `supabase/functions/send-delivery/index.ts` changes exist (executive stat row, sample rows, upsell block). Finish, test, commit.
3. **n8n contractor outreach workflow** — uncommitted local files exist: `docs/n8n-workflows/nyc_contractor_outreach_manual.json`, `scripts/leadcurate/nyc_contractor_outreach_seed.py`, `supabase/migrations/20260707133000_contractor_outreach_queue.sql`. Manual-trigger ONLY. Finish, test, commit.
4. **Nationwide verified-vacant column mapper** — refactor `scripts/leadcurate/process_verified_vacant.py` for a per-county column map. Target next: Wake NC, Guilford NC, Fulton GA, Marion IN — and now Hamilton TN (item 1) is a real-world test case for this.

## Payment status (do not re-litigate — this is done)

Both rails deployed and tested (Codex, 2026-07-07): `orders` + `payments` tables live, `payment-confirmation` Edge Function v1 deployed with token auth. Manual Cash App/Zelle and Stripe Payment Link both write the same order/payment record. **Only Derrick's provider pick is outstanding** — do not rebuild this.

## Soft-open pricing (locked 2026-07-07, do not re-litigate)

Tier 1 Hot Sheet $497 · Tier 2 Fresh Triggers $199/mo · Tier 3 Breaking Point $249 · Tier 4 Curated Distress $149 ($99 first 5 via `?price=99` on the quote template) · Tier 5 Ground Floor $299/report · Verified Vacant $149/county · Contractor cut $199 borough+class / $349 citywide · Asset Locator $750/file / $1,500 custom book. Baked into `docs/tiers/index.html` and `docs/quote-template/index.html`. **NOT on the public landing page** — quoted-with-preview + waitlist only, until Derrick's final confirm.

## Recently closed (for context, not action)

- Dead auction cron (Mecklenburg/Fulton/Wake, 0-row silent failure) disabled by Codex 2026-07-07.
- Asset Locator generalized (`scripts/leadcurate/asset_locator.py`), tested on Mecklenburg.
- NYC DOB cut tool got `--borough`/`--class` flags, tested on Brooklyn facade.
- Annual billing toggle hidden on landing page (both `site/index.html` and live `docs/site/index.html`).
- 4 new NC/SC markets (Gastonia, Concord, Rock Hill, Lancaster) added to intake form + property-numbers audit.
- `AGENT-OPERATING-RULES.md` got a "Sync discipline" rule + Vacant Land differentiation doctrine (2026-07-08) — read that file, it's short.

## Pending on Derrick only

- Payment provider pick (Stripe live vs. manual Cash App/Zelle).
- Send outreach scripts (land groups → NYC facade contractors → Charlotte collection attorneys).
- ~1hr attorney review before first law-firm (Asset Locator) sale.
- Ground Floor pricing lock, ad carousel pick, Private Market Engine strategy review.
