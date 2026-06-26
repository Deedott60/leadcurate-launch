# 🟢 LeadCurate Cheat Sheet 🟢

> Bookmark this file. It's a labeled index of every important file + simple instructions for starting new sessions and sales work.

---

## Section 1 — What every file does (labeled, no jargon)

### Files at the repo root (`leadcurate-launch/`)

| File | What it is | When to look at it |
|---|---|---|
| **`CLAUDE.md`** | The master LeadCurate file — 4-tier system, brand voice, customer flow, agent roles, current state. Auto-loaded by Claude every session in this folder. | Never need to open manually — Claude reads it automatically |
| **`LEADCURATE-CHEAT-SHEET.md`** | This file — your labeled quick reference | When you forget where something is |
| `README.md` | GitHub project description | Public-facing, not for daily use |

### Files inside `docs/`

| File | What it is | When to look at it |
|---|---|---|
| **`docs/AGENT-OPERATING-RULES.md`** | Universal rules for any agent (Claude, Codex, Hermes) — verification, communication, no test data in prod | Codex reads this before working |
| **`docs/codex-handoff-2026-06-25.md`** | Codex's current task list | When you want to know what Codex is doing |
| **`docs/THE-PLAN.md`** | Phase 1 / 2 / 3 sequence | When you want the big-picture roadmap |
| **`docs/OUTREACH-PLAYBOOK.md`** | Sales templates, message scripts | When you're sending outreach |
| **`docs/session-handoffs/`** | Date-stamped handoff files from prior sessions | When starting a new session, read the most recent one |
| **`docs/intake/index.html`** | Live intake form code | Don't edit unless you mean to |
| **`docs/packages/index.html`** | Customer-facing 4-tier overview (no prices) | Send link to prospects after intake |
| **`docs/tiers/index.html`** | Internal tier reference (with prices) | YOUR reference only — don't send to prospects |
| **`docs/quote-template/index.html`** | Personalized per-prospect quote | Generated from dashboard, sent to prospect |
| **`docs/command/index.html`** | Operator dashboard | Your daily ops view |

### Files outside this repo (your personal Claude setup)

| File | What it is | When to look at it |
|---|---|---|
| `C:\Users\lenovo\.claude\CLAUDE.md` | UNIVERSAL Claude rules (works for ANY project) | Auto-loaded every session |
| `C:\Users\lenovo\.claude\rules\verification-discipline.md` | The "verify before claiming" rule | Auto-loaded every session |
| `C:\Users\lenovo\.claude\rules\*.md` | Other universal rules | Auto-loaded every session |
| `C:\Users\lenovo\.claude\projects\.../memory\MEMORY.md` | Index of all my memory about you | Auto-loaded every session |

---

## Section 2 — How to start a NEW Claude session and pick up where we left off

When your conversation gets too long and you want a fresh context window:

1. **Before clearing:** Say to me — *"Save the handoff."* I'll write today's date-stamped file to `docs/session-handoffs/`
2. **Then `/clear`** or close + reopen Claude in the LeadCurate folder
3. **New session opens** → CLAUDE.md auto-loads → universal rules auto-load → memory auto-loads → I'm caught up on the LOCKED stuff in seconds
4. **First message to new session:** *"Read the latest session handoff and catch me up."* I'll read the most recent file in `docs/session-handoffs/` and tell you where we paused

**That's it. Two phrases. Locked stuff + handoff = nothing lost.**

---

## Section 3 — How to start sales work (when domain + Hostinger n8n are done)

Once domain lands and Codex finishes his tasks:

1. **Send the intake link** to a prospect (Facebook DM, IG, BiggerPockets, email):
   - Link: `https://deedott60.github.io/leadcurate-launch/intake/`
   - Or copy from dashboard → "Send intake link"

2. **Wait for them to fill it out** → notification lands in your inbox + auto-appears in dashboard Pipeline

3. **Read their answers** in dashboard → decide which tier fits using the picker logic in CLAUDE.md §5

4. **Go to dashboard → "Send a quote"** → fill in:
   - Buyer name
   - Market they want
   - Tier (dropdown) — pick the one that matches their intake
   - Click "Build quote link"
   - Copy the URL it gives you

5. **Send the quote URL** to the prospect (same DM/email thread)

6. **They click → see ONE clean offer** with their name + market + price + Confirm button

7. **They hit Confirm** → name + phone → email lands in your inbox

8. **Send payment instructions** (Cash App / Zelle / Stripe)

9. **After payment** → Ship the branded XLSX within 24 hours (you or me builds it)

**That's the whole flow. You're the operator. I'm the brain. Codex is the engineer. Hermes is the ops.**

---

## Section 4 — One-liners for common actions

| When you want to... | Say to me / type |
|---|---|
| Save where we are tonight before clearing | "Save the handoff" |
| Catch up after a new session opens | "Read the latest session handoff" |
| Update Hermes with new brand info | "Sync Hermes" |
| Send Codex a new task | I post it via Conference Room, you don't lift a finger |
| Get a new quote URL for a prospect | "Build a quote for [name], [market], Tier X" — or just open the dashboard "Send a quote" page |
| Stop Codex from doing something | "Tell Codex to stop [task name]" |
| Check what Codex is currently doing | "Check Codex status" |
| See today's full progress log | "Show today's commits" |

---

## Section 5 — Universal rules vs LeadCurate rules (the difference)

| Universal — applies to EVERY project | LeadCurate — only this project |
|---|---|
| Verify before claiming a system fact | The 4-tier product system |
| Honest > confident-sounding | Brand voice (no "cheap/save/less") |
| Match response shape to question | Customer flow (intake → quote → confirm → ship) |
| Never commit secrets | Pricing ($397/$197/$249/$149) |
| Token efficiency | Markets ready to sell |
| Frontend quality basics | Tier names (Hot Sheet / Fresh Triggers / Breaking Point / Curated Distress) |

If something is a UNIVERSAL rule, it goes in `C:\Users\lenovo\.claude\`. If it's LEADCURATE-specific, it goes in `CLAUDE.md` at this repo's root.

---

## Section 6 — When you're confused

Open this file (`LEADCURATE-CHEAT-SHEET.md`). It's the only file you need to remember.
