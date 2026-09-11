# Workforce OS — Canonical Agent Handoff

> **Canonical Concise Reference:** Read this file before undertaking any Workforce OS tasks, modifications, or database operations.

---

## 1. Core System Locations & Access

- **Live Standalone Workspace:** `https://leadcurate.com/workforce-os/`
- **Workforce OS UI / Client Code:** `docs/workforce-os/index.html`
- **LeadCurate Link:** `docs/command/index.html` links out to the standalone workspace; Workforce OS is not managed through the generic Projects screen.
- **Data Project ID:** `0fba0555-5ef0-455d-8bed-5a518db639c0` (project slug: `reentry-workforce-transition`, name: `Workforce OS`)
- **Program Source Files — THE SINGLE SOURCE OF TRUTH:** `/root/workforce-training` on Danny VPS (`76.13.25.117`, SSH alias `leadcurate-vps`).
- **Entry point for every agent:** read `/root/workforce-training/README.md` FIRST, every time, before building anything. It is the pathway file. Then read the current master document.
- **Current authority:** `/root/workforce-training/current/MASTER_DOCUMENT_2026-09-10.pdf` (v2). Anything dated 2026-09-09 or earlier is in `archive/` and is history, not authority. `/root/cowork-handoff/from-claude/` is stale.
- **Version control:** `/root/workforce-training` is a git repository mirrored to **https://github.com/Deedott60/workforce-training** (private). Commit and push after every meaningful change so the other agents pick it up.
- **One folder, no parallel copies.** Claude, Danny/Hermes, Astra and Codex all read and write this same folder. If a file in it is out of date, update it in place and move the superseded version to `archive/`. Do not leave two versions of a document side by side and do not start a competing copy elsewhere.
- **Folder layout:** `README.md` pathway · `AGENTS.md` operating rules · `PROJECT_CONTEXT.md` state and change log · `current/` the one governing master document · `archive/` superseded versions · `courses/sales/` and `courses/business/` syllabi, objectives, overviews and `modules/` lesson plans · `facilitator/` interview notes, glossary and foundation (Derrick only) · `participants/` what participants receive · `outreach/dylan/` career center track and `outreach/michael/` WIOA reentry track · `handoffs/` agent handoff briefs · `reviews/` agent review passes · `assets/` images
- **Same umbrella, two talking tracks:** Michael introduced Derrick to Dylan. Same workforce world, same folder, same course architecture. Only the framing differs — Dylan gets the general career center pitch with **no reentry or criminal record angle**, Michael gets WIOA and lived experience. Separate the framing, never the files.
- **Current editing authority, September 11:** Derrick's `Desktop/TRAINING_BUSINESS/` contains the latest learner portal and curriculum. Sync it to `/root/workforce-training` and the private workforce-training repository after editing. Do not overwrite local changes with an older server copy.

---

## Current share destinations

Use the Share links block at the top of Workforce OS to open or copy these URLs:

- `https://leadcurate.com/portal/`
- `https://leadcurate.com/overview/`

The root homepage also links to these two. The standalone Reentry page is not public; Reentry remains inside the learner portal. The playbook has six stages. Preserve Derrick's hand-edited Desktop sources and read `portal/RELEASE.md` in the private source folder before rebuilding.

## Learner portal deployment

- Learner URL: `https://leadcurate.com/portal/`.
- Generated public artifact: `docs/portal/index.html`, copied byte for byte from `OPEN_LEARNER_PORTAL.html` in the private workforce-training source folder. Rebuild there with `python portal/build.py` before copying. Do not edit the public artifact independently.
- Confirmed GitHub Pages configuration: `main` branch, `/docs`, custom domain `leadcurate.com`. This is the same deployment pattern as `docs/command/index.html`. The nginx IP fallback is not the custom-domain production host.
- The existing `/command/?page=workforce` route redirects to `/workforce-os/`. Launch links belong on that standalone Workforce OS page.
- Register this URL in `project_assets` for the Workforce project. The existing database constraint accepts `tool_instance`, not `portal`; use `tool_instance` with status `available`. Do not expand the schema for this asset.
- Only the generated learner HTML is public. Facilitator files, archives and working source remain in the private repository. Learner writing and progress stay in each browser and are not synced to Supabase.

## 2. Key Partners & Relationship Focus

- **Dylan Lehr**: General Career Center / sales-course-first focus.
  - Organization: Two Hawk Employment Services / NCWorks Career Center.
  - Operational objective: General Career Center discussion led by the four-module, eight-session Sales Career Course with applied AI embedded (course naming is not settled).
- **Michael S. Coone**: WIOA / reentry discovery focus.
  - Organization / Title: Michael S. Coone, Gaston County Workforce Development Board Director / Assistant Director of Social Services.
  - Operational objective: Workforce Innovation and Opportunity Act (WIOA) alignment, discovery of current WIOA/reentry services and where Derrick's training could fit, and community transition discovery.

---

## 3. Data Model & Architecture Discipline

All Workforce OS data mutations and queries executed by future agents must bind directly to project ID `0fba0555-5ef0-455d-8bed-5a518db639c0`:

1. **`project_items` Table**:
   - Action items, milestones, and dynamic partner relationship cards must be recorded here.
   - Dynamic partner relationship records use `kind: 'relationship'`.
   - Never use `localStorage` as a source of truth.
2. **`project_assets` Table**:
   - Curriculum documents, session syllabi, portal tools, and product asset references must be registered as rows bound to this project ID.
3. **`activity_feed` Table**:
   - All status updates, milestones, blockers, and agent handoffs must be logged with `project_id = '0fba0555-5ef0-455d-8bed-5a518db639c0'` and appropriate `target` (`claude`, `hermes`, `codex`, `derrick`, or `all`).

---

## 4. Privacy, Security & Hosting Discipline

- **Internal Files Are NOT Public Links:**
  - Program source files under `/root/workforce-training/current` on the Danny VPS are internal server filesystem paths.
  - Never render raw VPS filesystem paths (e.g. `/root/...`, `/opt/...`, or `file:///...`) as public browser `href` links in the client dashboard.
  - Internal files cannot be treated as public links until securely hosted on an authorized domain/storage endpoint.
