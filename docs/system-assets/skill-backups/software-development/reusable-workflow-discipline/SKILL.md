---
name: reusable-workflow-discipline
description: Use when a task produces a repeatable workflow, user correction, tool setup, business process, agent bridge, deployment pattern, or troubleshooting sequence that should not be relearned. Enforces creating or patching Hermes skills instead of leaving knowledge only in chat or notes.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, reusable-workflows, memory, cost-control, discipline]
---

# Reusable Workflow Discipline

## Overview

Derrick's explicit requirement: Hermes must not make him pay to reteach the same workflows. The whole point of the harness is reusable procedures that improve over time.

Use this skill whenever work involves a process likely to repeat, especially business setup, landing pages, GitHub deploys, agent coordination, Obsidian workflows, media generation, client/company workflows, SSH/tunnel setup, or debugging a recurring tool problem.

## Rule

Notes are not enough.

- Obsidian = shared project context and coordination.
- GitHub = source/code/assets/proof.
- Memory = small durable user/environment facts.
- Hermes skills = repeatable workflows and procedures.

If the user had to explain a process, correction, or preference more than once, it probably belongs in a skill.

## When to create a skill

Create a new skill when:

- a workflow takes 5+ tool calls or meaningful iteration,
- a setup/troubleshooting sequence was discovered,
- a user correction changes how future work should be done,
- a business or creative workflow will recur across projects,
- an agent coordination process is established,
- a tool/provider integration is configured,
- the same type of task is likely to appear for another company/client.

## When to patch an existing skill

Patch a skill immediately when:

- it was loaded and missed an important step,
- commands were wrong or incomplete,
- a new pitfall was discovered,
- the user corrected taste, strategy, or workflow,
- verification steps were missing.

Do not wait until the end of a long session if the missing instruction could affect the next action.

## Required final check after complex work

Before finalizing complex work, ask internally:

1. Did we discover a reusable workflow?
2. Did we rely on a skill that needs patching?
3. Is this knowledge currently only in chat/Obsidian/GitHub docs?
4. Would Derrick have to reteach this next time?

If yes, create or patch a skill before final response.

## Frustration handling rule

Strong user frustration is a workflow signal, not just emotion. If Derrick says he is wasting money, hitting rate limits, repeating himself, or asks for yes/no/no-more-explaining, immediately switch to: answer first, act second, explain last. When a fix is possible with tools, do it. When direct action is blocked, state the single missing artifact and provide one concrete workaround. Then update the relevant skill so the same failure mode does not repeat.

Do not keep naming blockers without moving the system forward. If the user says “stop telling me the problems,” respond with the next executable step, a copy/paste message, or a tool action already performed. Avoid architecture explanations until after the immediate unblock is handled.

See `references/frustration-cost-control.md` for the concise response pattern and anti-patterns.

## Verification checklist

- [ ] Relevant skill loaded before work.
- [ ] New repeatable workflow saved as a skill.
- [ ] Existing skill patched if it was incomplete.
- [ ] Proof provided: skill name and what changed.
- [ ] User not asked to repeat information already captured in a skill/note/repo.
- [ ] Setup claims verified from the target environment, not just dashboard/UI appearances.
- [ ] If a troubleshooting path loops twice, stopped and switched to a simpler workaround.

## Phone-only / low-bandwidth execution

When the user is on a phone or driving, do not give multi-command terminal blocks for the user to run. Either provide one short message they can forward to the local agent, or act through an existing bridge/tool. If the next step is a UI click, say the exact click only. Avoid repeating architecture or background unless asked.

## Common pitfalls

0. **Troubleshooting loop under frustration.** If Derrick says “you are not listening,” “stop telling me problems,” or “what exactly do I do,” stop repeating the same path. State the verified state in one line, choose the simplest next action that reduces required user effort, and avoid asking for more UI interpretation unless absolutely necessary. If a previous instruction created confusion, explicitly stop that path and switch to a different verified workaround.

1. **Saving only Markdown notes.** Notes are useful but do not automatically load as procedural memory. Create a skill for workflow.
2. **Assuming curator creates skills.** The curator manages skill lifecycle; it does not magically write missing workflows.
3. **Waiting for permission after every correction.** If the correction is clearly durable and reduces future waste, save or patch the skill.
4. **Making skills too project-specific when the pattern is broader.** Capture both general workflow and project-specific references when needed.
5. **Claiming “I’ll remember” without using tools.** Durable workflow memory requires `skill_manage`.
