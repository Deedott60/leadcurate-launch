---
name: safe-mutation-loop
description: "Make the smallest change possible, verify immediately, and roll back fast if proof is weak. Use before any multi-file, config, or generation-heavy work."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [verification, checkpoints, rollback, discipline, edits]
---

# Safe Mutation Loop

Use before any meaningful mutation: multi-file edits, config changes, installs, data migrations, expensive generations, or broad repo changes.

## Loop
1. Inspect current state
2. Name the exact target files or systems
3. Make the smallest proof change possible
4. Verify immediately with a tool
5. If results are weak or ambiguous, stop widening scope
6. Roll back or reset quickly instead of compounding bad changes

## Rules
- Proof before confidence
- Smallest useful step first
- Do not stack five speculative changes before checking one
- Expensive generations should start with a proof shot/proof scene/proof frame when possible
- If the user has already said stop, do not continue the loop

## Verification prompts
- Did the change actually do what was claimed?
- Is the proof current, not stale output sitting on disk?
- Is this worth scaling up or should it be abandoned?
