---
name: site-navigation-automation-stack
description: "Use the strongest available browser stack in this environment: Hermes browser tools first, then Playwright/Scrapy/xurl/browser-use when the task needs stronger scripted control."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [browser, automation, playwright, scraping, navigation]
---

# Site Navigation Automation Stack

Use when Derrick needs strong website navigation, scraping, or repeatable browser automation.

## Preferred stack order
1. Hermes browser tools for quick inspection/clicking
2. Playwright for scripted dynamic browser workflows
3. Scrapy for structured repeated crawling
4. xurl for X API workflows when authenticated
5. browser-use / operator tools for harder GUI/browser tasks

## Rules
- Choose the lightest tool that can reliably do the job.
- If screenshots are not enough, escalate to stronger browser automation.
- If a workflow needs repetition, prefer code over manual clicking.
- Distinguish public scraping from authenticated/API workflows.

## Deliverable
State which layer was used and why.
