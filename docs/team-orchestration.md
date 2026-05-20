# Team orchestration

LeadCurate coordination model for Derrick, Ella, Danny, and Codex.

## Roles

- Ella: local orchestrator, browser operator, repo manager, planner, and execution lead on Derrick's machine.
- Danny: VPS operator, remote worker, builder, deployer, and always-on automation helper.
- Codex: coding agent for implementation, refactors, reviews, and batch code tasks.
- Derrick: final decision-maker and operator.

## Operating rules

- Use this repo as the shared source of truth.
- Use GitHub issues for requests and PRs for implementation.
- Use docs files for current state, decisions, and next actions.
- Do not paste secrets or tokens into chat.
- Use SSH keys, GitHub login, or local CLI auth flows instead of sharing credentials in chat.
- Keep one active owner for each task.

## Shared state files

- `docs/current-state.md` — what is true right now.
- `docs/next-actions.md` — the next actionable step.
- `docs/ella-handoff.md` — longer operating context for Ella.

## Handoff pattern

1. Update `docs/current-state.md`.
2. Update `docs/next-actions.md`.
3. Create or update a GitHub issue or branch if work needs implementation.
4. Danny or Codex picks up from the shared state.

## Default rule

When in doubt, Ella orchestrates, Danny executes remote work, and Codex handles coding work inside the repo.