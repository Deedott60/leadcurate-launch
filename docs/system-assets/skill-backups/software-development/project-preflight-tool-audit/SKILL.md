---
name: project-preflight-tool-audit
description: "Before starting any project execution, force a preflight pass: define goal, required tools, missing tools, cheaper substitutes, and execution order before doing work."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [preflight, planning, tools, execution, discipline]
---

# Project Preflight Tool Audit

Use before starting any meaningful build, automation, commercial, data workflow, portal, or business system.

## Core rule
Do **not** start execution until the tool check is done.

The agent must first answer:
1. What is the exact goal?
2. What output are we trying to produce?
3. What tools are required?
4. Which of those tools are already available?
5. Which are missing?
6. What cheaper substitute can be used if a premium tool is unavailable?
7. What is the execution order?
8. What should be proven with a small test before spending more?

## Required preflight output
Before execution, produce a short checklist with:
- project name
- target deliverable
- required tools
- available tools
- missing tools
- fallback tools
- first proof step
- stop condition if the tool stack is not good enough

## Execution discipline
- If a critical tool is missing, say so before spending.
- If the workflow depends on a tool that is weak for the job, do not pretend otherwise.
- Prefer small proof-of-capability tests before full production.
- If the user is on a budget, separate draft stack from final stack.

## Mechanic analogy
Treat each project like a mechanic checking tools before the job:
- brake job -> confirm brake tools first
- engine swap -> confirm hoist/tools first
- premium commercial -> confirm video model, voice stack, editor, and assets first

## Final rule
No “let’s just try it” when the missing tool problem is already obvious.
