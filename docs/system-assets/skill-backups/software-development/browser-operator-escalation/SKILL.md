---
name: browser-operator-escalation
description: When a task depends on seeing or operating an actual video/post/web app, stop pretending screenshots are enough and escalate immediately to stronger browser/operator workflows or ask for the exact URL/file.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [browser, operator, escalation, verification]
---

# Browser Operator Escalation

Use when the user needs the agent to inspect or operate a real webpage, video, or browser-only workflow.

## Rules
- Do not claim to have seen a full video from screenshots.
- If the exact post/video/page matters, require one of: exact URL, direct file, or a connected browser/operator path.
- If screenshots are all that exist, state clearly that analysis is frame-based only.
- Do not push download/manual extraction back to the user if a reachable public URL can be tried first.
- If current browser tools are insufficient, say so plainly and stop overclaiming.
- Prefer proof over confidence.
