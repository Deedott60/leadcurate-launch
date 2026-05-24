---
name: obsidian-agent-bridge
description: Use when Derrick needs local Ella and VPS Danny to coordinate without copy/paste. Sets up/uses an Obsidian Markdown task board with a no-agent script watcher to avoid token burn.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [obsidian, multi-agent, coordination, cron, no-agent]
---

# Obsidian Agent Bridge

## Overview

Use this workflow when the user wants multiple Hermes agents (for example Ella on a local laptop and Danny on a VPS/Telegram gateway) to hand work to each other without the user copy/pasting between chats.

The bridge is a shared Obsidian-compatible Markdown vault plus a script-only watcher. The watcher must be `no_agent=True` so it does not spend LLM/model tokens just to check for tasks.

## Canonical paths for Derrick's LeadCurate setup

- Shared vault: `/root/ObsidianVault`
- Task board: `/root/ObsidianVault/Agents/Task Board.md`
- Ella/Danny bridge note: `/root/ObsidianVault/Agents/Ella Danny Bridge.md`
- Script watcher: `~/.hermes/scripts/check_danny_task_board.py`
- Watcher job name: `obsidian-danny-task-board-alert`

## Task board format

Tasks for Danny go under `## Danny Inbox` in the task board.

Use this exact block format:

```markdown
### TASK: short title
Assigned to: Danny
Status: open
Priority: normal
Requested by: Ella
Created: YYYY-MM-DD HH:MM

Task:
What Danny needs to do.

Success criteria:
How we know it is done.
```

When Danny finishes manually or via a task run, update the block with `Status: done` or `Status: blocked` and add `Result:`.

## No-agent watcher pattern

Use Hermes cron with `no_agent=True` and a Python script that:

1. Reads the task board.
2. Finds `Assigned to: Danny` + `Status: open` task blocks.
3. Hashes the open-task set.
4. Sends output only when the set is new/changed.
5. Prints nothing when there is nothing new, so no Telegram spam.

This costs no LLM/model tokens because it never launches the agent.

Example creation:

```python
cronjob(
  action='create',
  name='obsidian-danny-task-board-alert',
  schedule='every 3m',
  no_agent=True,
  script='check_danny_task_board.py',
  deliver='origin'
)
```

The script path must be relative to `~/.hermes/scripts/`, not absolute.

## Important distinction

A Hermes cron job is not visible in Linux crontab, systemd, or `ps` as a persistent process. To verify, use `cronjob(action='list')` or `hermes cron list`, not `crontab -l`.

## Workflow

1. Ella writes a task into the board.
2. The no-agent watcher detects it and alerts Telegram without token burn.
3. Derrick or Danny says `check task board`, or Danny manually opens the board and executes the task.
4. Danny records the result in the same board, including proof: file path, commit hash, preview URL, screenshot path, or command output.

## Outbound bridge fallback

If Danny cannot SSH into Ella because there is no reachable laptop route, but Ella can SSH outbound to the VPS, use a pull/run/push loop instead of continuing to argue about inbound SSH. Danny writes a command script on the VPS, Ella's local loop downloads and runs it, then uploads output back to the VPS. This enables user-level diagnostics and self-repair without inbound laptop access. Avoid sudo-required commands unless Derrick is physically present to approve/type the password.

See `references/leadcurate-ella-danny-bridge.md` for the exact incident notes and outbound bridge command pattern.

See `references/tailscale-and-outbound-bridge-pitfalls.md` for Tailscale duplicate-device pitfalls, Windows-first Tailscale setup, and when to stop trying direct SSH and fall back to the outbound bridge.

## Directness rule for frustrated users

When the user is already frustrated about the bridge or local-agent setup, do not keep explaining architecture. Give the exact current state in yes/no terms and the next concrete message/command to send. If direct SSH is not reachable, say so plainly, then provide the best available workaround that can run without the user being at the laptop (for example a repo-hosted self-repair script or outbound pull/run/push bridge). Do not repeat partial setup loops.

If the user asks “what do I do now?” while setting up Tailscale, answer with the single UI action: install **Windows Tailscale**, sign in, click **Connect**, send the `100.x.x.x` IP, then approve the VPS login link. Do not mention ACLs/IP sets unless the user is already in advanced admin settings and asks specifically.

If the outbound bridge is supposed to be running, verify it before answering by checking whether the outbox output updated after the inbox command changed. If it has not updated, the actionable response is: “the bridge loop stopped; restart it,” not another explanation of SSH/Tailscale.

## Laptop SSH reality check

Ella having SSH access into the VPS does not mean the VPS can SSH back into Ella's laptop. For direct repair of a local WSL/laptop agent, Danny needs a reachable route back to the laptop: Tailscale/ZeroTier, Cloudflare Tunnel, router port forward, or another remote-access channel. A WSL internal IP such as `172.x.x.x` is not enough from the VPS. If sudo/admin input is required and the user is only on a phone, switch to Obsidian/GitHub/self-repair script workflow until the user can enter the password.

### Tailscale setup pitfall

When using Tailscale to connect a VPS manager to a user's laptop, do not keep generating fresh `tailscale up` links if the user says the dashboard already shows the machine. Fresh auth links can create duplicate/stale Linux machine entries and frustrate the user. Verify from the VPS with `tailscale status` and `tailscale ip -4`; if the live daemon still says `NeedsLogin` while the dashboard shows green machines, stop the loop and choose a cleaner path: use an auth key, remove stale entries deliberately, or fall back to the outbound bridge. Do not tell the user to click “approve” again unless the CLI is actively waiting and you have a single current login URL.

### Outbound bridge manager limit

The outbound bridge lets Danny place command scripts on the VPS for Ella's laptop to pull/run/upload results. It is useful for user-level fixes and diagnostics without inbound SSH, but it is not the same as live SSH or managing Ella's reasoning. Use it to install rails, verify files, run audits, and create launchers; do not claim it makes Danny fully “Ella's manager.” For ongoing task quality, install/prompt skills like task-completion discipline and require proof artifacts.

## Session-specific references

See `references/leadcurate-ella-danny-bridge.md` for the condensed LeadCurate/Ella/Danny bridge incident, including what was actually working, what was blocked, and the no-agent watcher pattern.

See `references/tailscale-outbound-bridge-lessons.md` for the Tailscale duplicate-device pitfall, direct SSH requirements, and outbound bridge fallback pattern.

See `references/outbound-bridge-and-tailscale-escalation.md` for the outbound pull/run/push bridge pattern, the Tailscale escalation path, and phone-safe instructions for getting from a fragile bridge to real reachable access.

## Common pitfalls

- Do not run a full LLM agent every 3 minutes just to poll the board; that burns tokens.
- Do not tell the user the bridge is live until `cronjob(action='list')` verifies the watcher exists and is enabled.
- Do not expect Obsidian desktop GUI to matter on a headless VPS. The agent can use the Markdown vault directly.
- Do not claim Ella connected or did work without checking SSH logs, Git commits, bridge outbox output, or board notes.
- Do not keep generating fresh Tailscale auth links after the user says the dashboard already shows machines. Verify `tailscale status` from the VPS, explain stale/duplicate device state once, then either use an auth key/admin cleanup or stop and use the outbound bridge.
- Do not ask a phone-only user to paste commands into WSL. Give a message they can forward to the local agent, or use the outbound bridge if it is running.

## Verification checklist

- [ ] `/root/ObsidianVault/Agents/Task Board.md` exists.
- [ ] `OBSIDIAN_VAULT_PATH=/root/ObsidianVault` is set in `~/.hermes/.env` if Obsidian tools need it.
- [ ] `cronjob(action='list')` shows `obsidian-danny-task-board-alert` enabled.
- [ ] Watcher is `no_agent=True`.
- [ ] Test task triggers one alert and then stays quiet until changed.
