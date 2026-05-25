---
name: tmux-session-operations
description: "Use tmux as the default session-control layer when work involves multiple long-running terminal tasks, persistent shells, or parallel agent/operator workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [tmux, sessions, multitasking, terminals, organization]
---

# tmux Session Operations

Use when work involves more than one active terminal context or when losing terminal state would hurt.

## Trigger conditions
Use tmux when any of these are true:
- multiple long-running commands
- background watchers/log tails
- one shell needs to stay open while another does work
- multi-agent / multi-pane terminal organization would reduce confusion
- a process needs persistent terminal state across checks
- a browser/operator tool may need its own shell later

## When not needed
Skip tmux for:
- one short command
- one-off file reads/writes
- simple scripts that finish immediately

## Default pattern
- one tmux session per project
- named windows per role:
  - app
  - logs
  - worker
  - ops
  - scratch
- use clear window names, not defaults
- do not leave mystery sessions unnamed

## Rule
Before running multiple persistent terminal tasks, ask internally:
- would tmux reduce confusion or lost state here?
If yes, use it.
