# Agent Operating Rules — Read Before Every Task

> Applies to every agent working in this repo: Claude, Codex, Hermes, and any future agents.
> These are universal behaviors, not LeadCurate-specific. For LeadCurate-specific rules, see `/CLAUDE.md`.

---

## Verification discipline

- **Verify before claiming.** Do not state a system fact (broken/working/installed/has X records) without checking current state in this session. SSH-check, count-check, grep-check, or curl-check.
- **Honest over confident-sounding.** If you can't prove something with available tools, say "I can't verify this" — don't dress hypothesis as guarantee.
- **Old notes ≠ current state.** Task lists, memory files, prior commits, and skill files can be stale. Re-verify before acting.
- **Don't double down on stale claims.** If the operator pushes back, assume they're right and verify the system — don't defend the stale note.

## Sync discipline — no decision stays in one session

- **The moment Derrick decides something (pricing, strategy, product differentiation, a new rule), it goes into a durable file AND gets posted to the Conference Room in the same session — not "next time," not "if asked."** Derrick should never have to repeat a decision to a different agent.
- Strategy/product doctrine goes in this file or `/CLAUDE.md`. One-off task orders go in a `docs/codex-handoff-*.md` + `conf:role` post. Both, if it's a decision other agents need to act on AND remember long-term.
- Before ending any session where a decision was made, ask: "Does Codex know this? Does Danny know this? Is it written down anywhere they'll actually read?" If no to any of those, fix it before stopping.

## Product doctrine — Vacant Land differentiation

The competitive problem: static vacant-land lists (what most resellers and SMS-campaign data vendors sell) get built once and never rechecked. By the time a buyer acts on a record, a meaningful share of it is stale — already built on, already under contract, or was never actually vacant (a bad flag in the source file, or land carrying an improvement the list didn't catch).

Our answer: every Verified Vacant Land record is checked against the county's **current** parcel file before it ships — not a one-time scrape. The verification process (`scripts/leadcurate/process_verified_vacant.py`) runs multiple live checks (vacancy flag, land-vs-building value ratio, year built, heated area, owner, acreage) so a "vacant" record is actually vacant and actually buildable. Absentee owners get flagged specifically, since they're the ones structurally more likely to sell rather than build or hold.

**This is internal doctrine, not customer-facing copy.** Customer-facing material (audits, sample deliveries, sales messages) should describe the *outcome* — "you're not wasting outreach on land that's already gone or was never really vacant" — never the specific checks or scoring logic. That process is the moat; don't let it end up in something a prospect can copy-paste into their own script. See `docs/CURRENT-HANDOFF.md` for the active work generalizing this to new counties.

## Customer-facing writing style — LOCKED, non-negotiable

- **Never use an em dash (—) or en dash used as a connector in anything a customer reads** — emails, audit pages, sample deliveries, sales copy, quote templates. Split into two sentences, or use a period/colon instead. Derrick has flagged this repeatedly (Hermes cleaned "AI-sounding em dashes" from audit copy 2026-07-03; raised again 2026-07-08 against email/audit copy) — an em dash left in customer-facing text reads as AI-generated and undermines the "custom-built, not automated" premium positioning. This is not a style preference, it's a brand-trust rule.
- **No signature uses a personal name in automated or agent-sent customer emails.** Sign as "The LeadCurate Team," never "Derrick." Reasoning: once sends can be triggered by Codex, Danny, or a workflow without Derrick personally reviewing each one, a personal name attaches him to interactions he didn't personally have. Decided 2026-07-08.
- Before shipping ANY customer-facing text (email, audit page, sample delivery, quote), grep it for `—` before calling it done. This is a two-second check, do it every time.

## Email template discipline — ONE template, no exceptions

`supabase/functions/send-delivery/index.ts` is the only email-sending code for LeadCurate. It renders every lane (debt, vacant land, asset locator, contractor cuts, anything future) through the SAME `renderSample`/`renderDelivery` functions, which build their content generically from `deriveNumbers()`/`recordValue()`/`genericSampleTable()` — never from a lane-specific hardcoded branch or a second render function.

**Why this rule exists:** on 2026-06-30 a good, richer template (stat cards, "By the numbers," "Working notes") was built and verified with real test sends for Wake County — then never committed. Every session after that (Claude, Codex, and Claude again on 2026-07-08) built its own one-off version from scratch, because nothing forced reuse of what already worked. The result: every customer-facing email looked different, which is exactly the kind of thing that makes a business look unprofessional and amateur.

**If a new lane needs a new field type** (e.g. something that isn't owner/address/value/acreage), extend `recordValue()` and `deriveNumbers()` to recognize the new field — do not write a new `render*` function. If you think you need a second render function, you're about to repeat the mistake; stop and extend the generic one instead.

## Scraping / data-pull playbook discipline

`docs/playbooks/county-data-pull.md` and `docs/playbooks/js-blocker-bypass.md` are the ONLY canonical scraping references. They live in this git repo specifically so Codex and Danny/Hermes can both read AND write them — a prior version lived only in a local Claude Code skill folder on Derrick's Windows machine, which neither Codex nor Danny could ever reach, so nothing learned ever got passed forward and every county got re-solved from scratch. Don't repeat that.

**Every time you crack a new county source or fix a broken URL, append it to `docs/playbooks/county-data-pull.md` (or the JS-blocker one, if that's the fix), commit, and push — before ending the session.** This is not optional and not "if you remember." A solved county that isn't written down is a county that gets re-solved at full cost next time, in tokens and in Derrick's patience.

## Communication discipline

- **Match response shape to question shape.** A two-word question gets a two-word answer. Don't add sections/headers/summaries to simple questions.
- **Show proof, not adjectives.** "Pushed commit `abc123`" beats "successfully updated."
- **State only what you did, not what you might have done.** No hypotheticals.

## Conference Room protocol

When you finish a task posted to your queue, post back:
```sql
INSERT INTO activity_feed (event_type, source, title, body, target)
VALUES ('conf:done', '<your-agent-name>', '<short title>', '<what you did + proof>', '<who asked>');
```

When you can't complete a task (blocked, unclear, missing dependency):
```sql
INSERT INTO activity_feed (event_type, source, title, body, target)
VALUES ('conf:blocker', '<your-agent-name>', '<short title>', '<what you need>', 'derrick');
```

When you need to stop something already in progress:
```sql
INSERT INTO activity_feed (event_type, source, title, body, target)
VALUES ('conf:urgent', '<your-agent-name>', 'STOP — <title>', '<reason and what to do instead>', '<target>');
```

## Repository discipline

- **Never commit secrets, API keys, passwords, tokens, cookies, or credentials.**
- **Never insert test/demo data into production tables** (prospects, leads, intake_requests, messages, activity_feed). If you need to test, SELECT-only or DELETE in the same transaction.
- **Never push directly to main if there's any uncertainty about scope.** When unsure, work in a branch and ask Derrick to merge.
- **Never bypass hooks, signing, or CI checks** unless Derrick explicitly authorizes it.

## Source of truth hierarchy

When information conflicts, trust in this order:

1. **Direct verification right now** (SSH output, file content, count query, curl response)
2. **`/CLAUDE.md`** at repo root (LeadCurate state, voice, tier system, customer flow)
3. **This file** (universal agent behaviors)
4. **`docs/CURRENT-HANDOFF.md`** — the single current-state file, edited in place. Also `docs/THE-PLAN.md` for phase strategy. Dated `docs/codex-handoff-*.md` files are archived in `docs/codex-handoff-archive/` — history only, never current state.
5. **Memory files / older docs** — useful for context, NOT for state claims

If memory says X and SSH says Y, Y wins. Update the memory.

## Failure-mode awareness (lessons preserved)

Past mistakes that should not repeat:

| Mistake | Cost | Prevention |
|---|---|---|
| Claimed "Hermes brain offline" from stale task list (2026-06-23) | Damaged trust, wasted credits | SSH-verify Hermes status before claiming offline |
| Quoted "14.2M records" without re-counting (2026-06-23) | Misrepresented actual ~80M | Re-count when number is load-bearing |
| Said "people post fresh requests on forums" without proof (2026-06-23) | Oversold an unproven Lead Scout hypothesis | If WebSearch only returns old results, say so — don't dress as fresh |
| Static "Reply A/B/C" buttons that weren't clickable | Wasted a build cycle | Real form inputs, not decorative divs |
| `hermes send` instead of `hermes chat` in watcher | Tasks logged but never executed | Read the CLI usage before scripting it |

When you encounter a new failure mode worth preserving, add it to this table.
