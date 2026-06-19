# Next actions

- Use `docs/leadcurate-agent-handoff/README.md` as the start-here file for any agent, audit, or continuation.
- Use `docs/leadcurate-agent-handoff/08-local-and-github-inventory.md` to confirm the canonical repo before importing files from older local folders.
- Use `docs/leadcurate-agent-handoff/09-data-pipeline-status.md` for the LIVE state of the data layer: what's pulled (20 of 24 markets, ~2.8 GB on VPS), the working URL catalog, the 3 active blockers needing Chrome MCP / browser automation, and the proven Discovery Snapshot processing pattern. UPDATE this file after each pull or fix so the next agent picks up clean.
- Replace legal placeholders in `site/terms.html`, `site/privacy.html`, `site/refund-policy.html`, and `site/compliance.html`.
- Choose and configure the landing page intake backend. Preferred path: custom endpoint -> Supabase `intake_requests` -> email alert.
- Create Supabase tables for `intake_requests`, workflow runs/events, raw files, exclusions, and quality checks.
- Pick the first pilot county and one lead lane.
- Download one lawful public-record source file and run `scripts/build_sample_batch.py`.
- Review the sample batch manually before using it in sales calls.
- Build the first operator-kit documents from `docs/leadcurate-agent-handoff/03-operator-kit.md`.
- Decide skip-trace and DNC/contact suppression providers before exporting contact fields.
- Keep GitHub updated after every meaningful file change.
