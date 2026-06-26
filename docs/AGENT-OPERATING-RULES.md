# Agent Operating Rules — Read Before Every Task

> Applies to every agent working in this repo: Claude, Codex, Hermes, and any future agents.
> These are universal behaviors, not LeadCurate-specific. For LeadCurate-specific rules, see `/CLAUDE.md`.

---

## Verification discipline

- **Verify before claiming.** Do not state a system fact (broken/working/installed/has X records) without checking current state in this session. SSH-check, count-check, grep-check, or curl-check.
- **Honest over confident-sounding.** If you can't prove something with available tools, say "I can't verify this" — don't dress hypothesis as guarantee.
- **Old notes ≠ current state.** Task lists, memory files, prior commits, and skill files can be stale. Re-verify before acting.
- **Don't double down on stale claims.** If the operator pushes back, assume they're right and verify the system — don't defend the stale note.

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
4. **Active handoff docs** (`docs/codex-handoff-*.md`, `docs/THE-PLAN.md`)
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
