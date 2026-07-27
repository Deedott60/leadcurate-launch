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

## Data freshness and quality gate — LOCKED 2026-07-15

LeadCurate competes on accuracy and quality. **Every market and every requested lane must use the newest official source available when the analysis or customer delivery is built.** A file already sitting on the VPS is a cache, not proof that it is current.

- Before processing any market or lane, check the live official source in the current session and identify its newest release. Do this separately for parcel, ownership, value, tax, foreclosure, probate, permit, violation, auction, and other event sources because their update schedules differ.
- Record the exact source URL, source-data date, retrieval date, and whether values or statuses are proposed, preliminary, current, supplemental, or certified in the output metadata.
- If a newer official file exists, pull it and rebuild the canonical data, every affected lane, all overlap counts, metadata, audits, and customer-facing totals. Never keep old numbers and merely change the date label.
- An older official release may be used only when no newer source exists or the newest source is genuinely inaccessible. State the exact age and limitation before delivery; post a blocker when the age would undermine the customer's use case.
- Never infer an event lane from unrelated parcel characteristics. If the current official source does not prove tax delinquency, foreclosure, probate, a violation, or another event, mark that lane unavailable instead of fabricating it.
- Final acceptance requires one row per parcel, zero unexplained duplicates, metadata counts computed from the file that ships, and a source date visible to the operator. Accuracy outranks speed, convenience, and previously completed work.

## Data quality gate — LOCKED 2026-07-24, applies to EVERY market and EVERY product

**No lane data reaches a human, paying or not, until it passes `scripts/leadcurate/qa_lane_gate.py`.** This is universal: Dollar Leads packs, premium territory deliveries, white-label client instances (Reggie), sample pages, free social samples, audit pages, and every market ever scraped or processed from now on. Deployed at `/opt/leadcurate/scripts/qa_lane_gate.py`.

```bash
python3 /opt/leadcurate/scripts/qa_lane_gate.py --all
python3 /opt/leadcurate/scripts/qa_lane_gate.py --root /opt/leadcurate/processed/wake-nc --all
python3 /opt/leadcurate/scripts/qa_lane_gate.py --market wayne-mi --lane tired-landlords
```

Exit code 1 means the lane is not sellable and not deliverable. It measures:
- **Owner-occupied contamination** in any absentee/landlord lane, ceiling 2%
- **Institutional owners** (government, church, school, bank, authority) in wholesale lanes, ceiling 1%
- **Front-of-file affordability**, ceiling 20% of the first 50 records above 10x the lane median, because a $5 pack receives the front of the file
- **Core field coverage**, owner, property address, parcel ID, floor 95%

**Why this rule exists:** on 2026-07-24 a pre-launch QA pass found `tired-landlords` was 84.9% owner-occupied in Mecklenburg, 71.0% in Cook, 35.4% in Massachusetts, 34.1% in Wayne. Real properties, wrong label, caused by exact-string comparison of property vs mailing address when counties format them differently (`14611 N C 73 HY` vs `14611 HIGHWAY 73`). Dallas was clean only because it retained `normalized_address()`. Nothing had sold yet, so no customer was harmed, but the store was hours from being promoted publicly. A rule alone would not have caught it; a measurement did.

**Corollaries:**
- Never mark a lane live, or hand a file to a client, on the basis that the pipeline "ran successfully." A clean run is not a clean product.
- When a lane fails, hold it (`status` change), do not delete it. Data is expensive, labels are cheap to fix.
- Report the measured number, not "fixed." "Mecklenburg tired-landlords now 1.4% owner-occupied" is proof. "Rebuilt the lane" is not.
- Adding a new market is not done when the scrape finishes. It is done when the gate passes.

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
| Built Dallas analysis from a 2025 file while an official 2026 source was available (2026-07-15) | Produced stale customer-facing counts and damaged trust | Check the live official source for every market and lane before processing; an existing VPS file is not freshness proof |
| Static "Reply A/B/C" buttons that weren't clickable | Wasted a build cycle | Real form inputs, not decorative divs |
| `hermes send` instead of `hermes chat` in watcher | Tasks logged but never executed | Read the CLI usage before scripting it |

When you encounter a new failure mode worth preserving, add it to this table.
