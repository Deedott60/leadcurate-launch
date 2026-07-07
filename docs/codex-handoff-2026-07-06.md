# Codex Handoff — 2026-07-06

**From:** Claude (orchestrator) · **Operator:** Derrick
**Supersedes:** `docs/leadcurate-agent-handoff/11-codex-role-and-current-state.md` (2026-06-21, stale)

## Your standing role (unchanged)

IT, security, code quality, pipeline engineering. Claude owns business/copy/design, Danny owns recurring ops + dashboard maintenance, Derrick owns pricing/payments/customer contact. Rules that still bind: no test data in live Supabase tables; manual-trigger-only on n8n delivery workflows; no pricing decisions; deliveries are email-only (never hosted customer pages).

## What changed since your last handoff

- Two new B2B lanes shipped 2026-07-06 with live sample pages + processed data:
  - **Asset Locator** (collection attorneys / judgment recovery) — Mecklenburg lien×parcel cross-reference, `/opt/leadcurate/processed/mecklenburg-nc/2026-06-19/mecklenburg-nc-enriched-city-liens-*.csv`
  - **NYC Code Violations** (restoration contractors) — `/opt/leadcurate/processed/nyc/2026-07-06/nyc-dob-active-restoration-*.csv`, built by `/opt/leadcurate/scripts/process_nyc_dob_restoration.py` (also in repo at `scripts/leadcurate/`)
- Vacant-land lane (land flippers) is being sold from the existing 2026-06-19 Mecklenburg processed file.
- Derrick is doing live voice-note outreach in wholesaler groups NOW. First sales could land any day. Payment method decision is imminent (Derrick's call, expected 2026-07-07).

## Your assignments, priority order

### 1. Payment readiness (prep only — do NOT pick the provider)
When Derrick picks Cash App / Zelle / Stripe tomorrow, everything downstream must be a 15-minute wire-up, not a build. Prep now:
- A Stripe Payment Link path (test mode) AND a manual-payment path (Cash App/Zelle) that both end in the same place: a `payments`/`orders` record in Supabase + `conf:status` post to activity_feed + trigger point for the manual_delivery_pipeline.
- Keep it manual-confirmation for non-Stripe (Derrick marks paid in dashboard → pipeline can run).

### 2. Fix or kill the dead auction-scraper cron
`crontab: 15 2 * * 0 /opt/leadcurate/scripts/run_auction_scrapers.sh` has written **0 rows** for Mecklenburg, Fulton, and Wake on its last runs (see `/opt/leadcurate/logs/auction_scrapers_*.log`). Diagnose (source layout changed? JS-blocked?) — fix if under an hour each, otherwise disable the cron and log the blocker. Silent 0-row automation is worse than no automation.

### 3. Generalize the asset-locator cross-reference
`lien/judgment file × parcel-owner file → matches with values + deeds URL` is now a sellable product. Turn the one-off Mecklenburg join into a reusable script (`scripts/leadcurate/asset_locator.py`) that takes (market, lien-source CSV, parcel CSV) and emits the standard full/preview/meta triple. Wake, Guilford, Cuyahoga, Jefferson KY all have both sides of the join already on disk.

### 4. NYC violations cut tool
Add a filter mode to `process_nyc_dob_restoration.py`: `--borough`, `--class` (facade/hazardous/boiler/structural/wwp), `--top N` so a paid order ("Manhattan facade top 500") is one command. Restoration buyers will order narrow cuts.

### 5. Continue prior pipeline work (from your 2026-07-04 list)
- Tarrant TX + Maricopa AZ extractor modules (raw ZIPs on disk, no extractor yet)
- Shelby TN deliverable parser (universal key exists; delivery-file builder still routes to review)
- Duval FL / Davidson TN source registration

## Report back
Post `conf:done` to activity_feed per completed item, commit with clear messages. Anything ambiguous → ask Derrick in the Conference Room, don't guess.
