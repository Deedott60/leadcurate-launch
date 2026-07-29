# Codex handoff — 2026-07-28 — Portfolio page + OS Career section

**From:** Claude (orchestrator)
**Branch touched:** `main` @ `leadcurate-launch`
**Status:** done and verified locally. Needs your attention only for the merge note in §4.

---

## 1. What was built

A public portfolio page for Derrick, positioning him as an operator who ships production software. It is the artifact he sends with job applications (currently applying to a Replit Mid-Market Account Manager role, among others).

**Live (private artifact, permanent URL):**
`https://claude.ai/code/artifact/87165dbb-c869-4418-860e-b6191e7bb74d`

**Source of truth for the page:**

| Path | Role |
| --- | --- |
| `C:\Users\lenovo\Documents\portfolio\template.html` | **Edit this.** Contains `{{IMG_*}}` tokens. |
| `C:\Users\lenovo\Documents\portfolio\shots\` | Source screenshots. |
| `C:\Users\lenovo\Documents\portfolio\index.html` | **Generated.** Do not hand-edit. |
| `C:\Users\lenovo\Desktop\Derricks portfolio\` | Offline copy for Derrick. |

Build step inlines the screenshots as base64 data URIs (the artifact host enforces a strict CSP — no external asset fetches, so everything must be self-contained). The build script currently lives in the session scratchpad; **if you touch this, move it to `scripts/build-portfolio.js` in the repo first** — it is the only un-versioned piece.

---

## 2. Change to `docs/command/index.html` (LeadCurate OS)

Added a **Career → Portfolio** section. Three edits:

1. New nav group after `Learning (for you)`:
   ```html
   <div class="nav-label">Career</div>
   <div class="nav-section">
     <div class="nav-item" data-page="portfolio">…</div>
   </div>
   ```
2. New `<div id="page-portfolio" class="page">` inserted after `page-templates`.
3. **`'portfolio'` appended to the hardcoded `pages` array** (~line 1486).

**Gotcha worth knowing:** step 3 is not optional. `window.nav()` iterates that array and calls `getElementById('page-'+p)` on each. A page not in the array never gets `.active`, so it silently stays `display:none` — the nav item highlights and nothing appears, with no console error. I hit exactly this. If you add pages later, update the array in the same commit.

Verified with headless Chrome: nav item present, page visible on click, no other page leaks visible, zero JS errors.

---

## 3. Privacy decisions — please do not undo these

Three things were deliberately kept off the public page:

1. **No dashboard screenshot.** The first capture of Command HQ contained a real inbound lead's full name, email and phone, a client company name, an invoice number, internal hostnames, a systemd port and an env var name. Replaced with a hand-authored 21-module inventory (text only, no counts).
2. **No blessing board screenshot** from `derrickandmiesha.leadcurate.com`. Guest names are **rendered into a canvas**, not the DOM — DOM scrubbing reports clean while the names survive in the pixels. A `innerText` check is a false negative here. If we ever want that board shown, the site needs a real placeholder-data mode; do not try to scrub it client-side.
3. **No phone number** on the page. Email + GitHub only, per Derrick.

---

## 4. Merge note — action for you

`docs/command/index.html` exists in three places and they have diverged:

| Worktree | Branch | Size |
| --- | --- | --- |
| `leadcurate-launch` | `main` | 164 KB → now larger (my edit) |
| `.worktrees/projects-os` | `codex/projects-os` | 191 KB (ahead) |
| `.worktrees/reggie-c1-c3` | `codex/reggie-c1-c3` | 161 KB |

**I edited `main` only.** `codex/projects-os` is ~27 KB ahead of main and is yours. When you next merge, carry the three edits in §2 forward rather than letting a whole-file overwrite drop them. The `pages`-array line is the one most likely to be lost in a conflict resolution, and its failure mode is silent.

---

## 4b. Added after first pass — F&B Manager (record 01)

A fifth project was added and made the **lead record**: an F&B management platform built for a **casino and resort client, in daily field use**. It is the only project on the page that a third party's operation depends on, which is why it leads.

**Confidentiality constraints — hard limits, do not relax on review:**

- Client name: **never**. Industry ("casino and resort") is approved; the client is not.
- **No screenshots, no UI, no interface description** beyond function.
- No identifying scale detail.
- Approved to state: inventory and par levels, scheduled check-ins, SOPs surfaced at point of work, a camera feature that reads stock from a photo, tablet-first. Stack: Next.js, React, Supabase, Postgres.

**No metrics anywhere on the page.** Derrick does not have real numbers yet and none were invented. If you review this, do not "improve" it by adding plausible-sounding figures — he has to defend every claim in an interview.

Record numbering shifted: F&B 01, Rooted 02, LeadCurate 03, White-Label 04, Derrick & Miesha 05. Masthead count and "short version" copy updated to five.

---

## 5. Open items (not started)

- **Real-estate client tool** — Derrick has screen recordings of a tool he built for a client. They were shared as Gmail attachment and Drive preview links, which require his session and cannot be fetched from the local machine. They are not on local disk (searched Downloads, Videos, Desktop, Documents). Blocked until he saves them locally. This is the biggest gap: it is the only client-facing project with no visual.
- **No outcome numbers** anywhere on the page — no customer counts, revenue, or time saved. For an account-management role this is a real weakness.
- **HyperFrames video** — requested, not built. Local toolchain fails `doctor`: FFmpeg errors on invocation (missing runtime DLLs), Chrome Headless Shell absent, no Docker. Derrick notes the VPS may have a working install — unverified, worth checking before anyone rebuilds the local toolchain.

---

## 6. If you rebuild the page

```bash
# from Documents/portfolio — edit template.html, then regenerate index.html
node scripts/build-portfolio.js   # once the script is moved into the repo
```

Verify before publishing: zero horizontal overflow at 1280 and 390 px, all images load, no JS errors, and the file stays pure ASCII (the page is served without a charset header in some contexts — non-ASCII characters render as mojibake, so JS strings use `\uXXXX` escapes deliberately).
