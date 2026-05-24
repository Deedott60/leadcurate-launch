---
name: memory-triage
description: "Classify new information into durable memory, user preference, project context, session recall, or discard so the agent stops polluting persistent memory."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [memory, triage, context, discipline]
---

# Memory Triage

Use after any substantive task, correction, or new user detail.

## Buckets
1. `USER` — stable preferences, communication style, recurring dislikes, roles
2. `MEMORY` — durable environment facts, conventions, tool quirks, project structure
3. `PROJECT CONTEXT` — belongs in repo docs, AGENTS.md, Notion, or business folders
4. `SESSION RECALL` — useful later but not always-on; leave it to session history/session_search
5. `DISCARD` — temporary logs, one-off outputs, stale execution details

## Rules
- Do not save temporary task state to persistent memory.
- Do not save anything already tracked better in repo docs or business indexes.
- If a fact will be stale in a week, it probably does not belong in persistent memory.
- Save only what reduces future user steering.

## Output discipline
Before saving anything, ask internally:
- Is this durable?
- Is this cross-session useful?
- Is this better stored somewhere else?
- Will this cause future confusion if injected automatically?

If the answer is uncertain, do not save it.
