# Workforce OS — Canonical Agent Handoff

> **Canonical Concise Reference:** Read this file before undertaking any Workforce OS tasks, modifications, or database operations.

---

## 1. Core System Locations & Access

- **Live Dashboard Route:** `https://leadcurate.com/command/?page=workforce`
- **Dashboard UI / Client Code:** `docs/command/index.html` (first-class `#page-workforce` container and `window.renderWorkforce*` methods)
- **Data Project ID:** `0fba0555-5ef0-455d-8bed-5a518db639c0` (project slug: `reentry-workforce-transition`, name: `Workforce OS`)
- **Program Source Files:** `/root/workforce-training/current` on Danny VPS (`76.13.25.117`, SSH alias `leadcurate-vps`)

---

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
