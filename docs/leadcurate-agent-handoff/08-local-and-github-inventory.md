# 08 - Local And GitHub Inventory

This file exists to prevent LeadCurate files from getting mixed with other local projects.

## Canonical source of truth

Use this repo and folder as the source of truth:

- Local canonical repo: `C:\Users\lenovo\Documents\Leadcurate\leadcurate-launch`
- GitHub repo: `https://github.com/Deedott60/leadcurate-launch.git`
- Main branch: `main`
- Agent start file: `docs/leadcurate-agent-handoff/README.md`

Any future agent should start in the canonical repo above.

## Known related local locations

These locations have appeared during the LeadCurate work:

- `C:\Users\lenovo\Documents\Leadcurate\leadcurate-launch` - canonical working repo, cloned from GitHub and pushed.
- `C:\Users\lenovo\leadcurate-launch` - older local checkout/historical source. Some n8n docs were recovered from here and copied into the canonical repo.
- `C:\Users\lenovo\Downloads\Claud Leadcurate bugfix.zip` - Claude bugfix bundle. The relevant site/legal fixes were extracted and applied into the canonical repo.
- `C:\Users\lenovo\Documents\Leadcurate` - parent workspace folder. This contains the canonical clone and an empty/old Git shell from earlier setup.

Treat every other LeadCurate-looking folder as non-canonical unless it is explicitly reviewed and imported.

## What has already been consolidated

The canonical repo now includes:

- landing page: `site/index.html`
- duplicate landing copy: `site/index_v2.html`
- legal pages: `site/terms.html`, `site/privacy.html`, `site/refund-policy.html`, `site/compliance.html`
- business plan: `docs/leadcurate-business-launch-plan.md`
- clean agent package: `docs/leadcurate-agent-handoff/`
- recovered n8n specs:
  - `docs/leadcurate-v1-n8n-spec.md`
  - `docs/leadcurate-n8n-first-county.md`
- sample batch workflow: `docs/sample-batch-automation.md`
- sample batch script: `scripts/build_sample_batch.py`
- starter Supabase schema: `supabase/schema.sql`

## What is not fully consolidated yet

These are still future tasks:

- full operator-kit documents
- real Supabase migrations beyond starter schema
- form intake endpoint
- email provider integration
- Stripe links
- selected skip-trace provider
- selected DNC/contact suppression provider
- first pilot county raw source file and generated sample batch

## Import rule for future agents

If another LeadCurate file is found outside the canonical repo:

1. Do not overwrite canonical files blindly.
2. Copy or inspect the file in a temporary comparison area.
3. Determine whether it is newer, duplicate, obsolete, or unrelated.
4. If useful, import it into the correct canonical folder.
5. Update this inventory, `README.md`, and `docs/next-actions.md`.
6. Commit and push to GitHub.

## Git status note

The older folder `C:\Users\lenovo\leadcurate-launch` may show Git safe-directory/dubious-ownership warnings from sandboxed tools. That is another reason to avoid using it as the active repo. Use the canonical repo in `Documents\Leadcurate\leadcurate-launch`.
