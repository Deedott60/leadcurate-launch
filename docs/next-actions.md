# Next actions

- Use `docs/leadcurate-agent-handoff/README.md` as the start-here file for any agent, audit, or continuation.
- Use `docs/leadcurate-agent-handoff/08-local-and-github-inventory.md` to confirm the canonical repo before importing files from older local folders.
- Replace legal placeholders in `site/terms.html`, `site/privacy.html`, `site/refund-policy.html`, and `site/compliance.html`.
- Choose and configure the landing page intake backend. Preferred path: custom endpoint -> Supabase `intake_requests` -> email alert.
- Create Supabase tables for `intake_requests`, workflow runs/events, raw files, exclusions, and quality checks.
- Pick the first pilot county and one lead lane.
- Download one lawful public-record source file and run `scripts/build_sample_batch.py`.
- Review the sample batch manually before using it in sales calls.
- Build the first operator-kit documents from `docs/leadcurate-agent-handoff/03-operator-kit.md`.
- Decide skip-trace and DNC/contact suppression providers before exporting contact fields.
- Keep GitHub updated after every meaningful file change.
