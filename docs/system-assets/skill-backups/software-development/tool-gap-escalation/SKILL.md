---
name: tool-gap-escalation
description: "When a task is blocked by a missing capability, stop arguing from the current toolset and explicitly check whether the capability can be installed, wired, or delegated before saying no."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [tools, escalation, installation, capability, discipline]
---

# Tool Gap Escalation

Use whenever Derrick asks for a capability and the current stack may not support it.

## Rules
1. Do not answer from assumption.
2. Check whether the capability already exists.
3. If not, check whether it can be installed locally.
4. If not, check whether it can be wired through an external service/account.
5. If not, check whether it can be delegated to another agent/tool.
6. Only after those checks, answer yes/no.

## Required answer format
- current capability: yes/no
- installable here: yes/no
- needs user access/account: yes/no
- best next step: one sentence

## Anti-failure rule
Never spend multiple turns debating a missing capability before checking the tool path.
