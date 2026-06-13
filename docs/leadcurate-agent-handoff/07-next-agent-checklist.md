# 07 - Next Agent Checklist

Use this checklist when another agent audits or continues the project.

## First orientation

- Read this folder first.
- Confirm `08-local-and-github-inventory.md` so you know which repo/folder is canonical.
- Then read `docs/leadcurate-business-launch-plan.md`.
- Then read `docs/leadcurate-v1-n8n-spec.md` if building automation.
- Then inspect `site/index.html` if working on the landing page.

## Immediate build tasks

1. Replace legal placeholders in legal pages.
2. Choose intake backend path: Supabase endpoint preferred.
3. Add Supabase migration for `intake_requests` and workflow tables.
4. Create form endpoint.
5. Connect landing page `FORM_ENDPOINT`.
6. Add email notification.
7. Create Stripe deposit/single-batch links.
8. Pick one pilot county and lane.
9. Download first lawful public source file.
10. Run `scripts/build_sample_batch.py`.
11. Review sample output manually.
12. Build first operator-kit documents.

## Audit questions

Ask:

- Can a new buyer understand what LeadCurate sells in 30 seconds?
- Does every claim avoid guaranteed deal language?
- Does the batch include source dates and score reasons?
- Are contacts excluded unless enrichment/DNC policy is ready?
- Does the backend preserve raw source files?
- Can records be blocked from resale during an active access window?
- Does the form save leads somewhere durable?
- Does the owner receive email alerts?

## Files to preserve

Do not delete without replacing:

- `docs/leadcurate-agent-handoff/`
- `docs/leadcurate-business-launch-plan.md`
- `docs/leadcurate-v1-n8n-spec.md`
- `docs/leadcurate-n8n-first-county.md`
- `docs/sample-batch-automation.md`
- `scripts/build_sample_batch.py`
- `supabase/schema.sql`
- `site/index.html`
- `README.md`
- `docs/next-actions.md`

## Consolidation rule

If a LeadCurate file is discovered outside `C:\Users\lenovo\Documents\Leadcurate\leadcurate-launch`, do not treat it as canonical automatically. Compare it, import only the useful parts, update `08-local-and-github-inventory.md`, then commit and push.

## Recommended next commit

After creating the first operator-kit docs, commit with:

```bash
git add docs/operator-kit docs/leadcurate-agent-handoff
git commit -m "Add LeadCurate operator kit materials"
git push origin main
```
