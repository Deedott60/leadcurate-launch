#!/usr/bin/env bash
set -euo pipefail

echo "== Danny self-repair: starting =="

# 1) Ensure curator is enabled so agent-created skills are tracked/managed
hermes config set curator.enabled true >/dev/null 2>&1 || true

# 2) Ensure Obsidian vault path is configured
mkdir -p /root/ObsidianVault/Agents /root/ObsidianVault/LeadCurate /root/ObsidianVault/Decisions
mkdir -p /root/.hermes
touch /root/.hermes/.env
if grep -q '^OBSIDIAN_VAULT_PATH=' /root/.hermes/.env; then
  python3 - <<'PY'
from pathlib import Path
p=Path('/root/.hermes/.env')
lines=p.read_text().splitlines()
lines=[('OBSIDIAN_VAULT_PATH=/root/ObsidianVault' if l.startswith('OBSIDIAN_VAULT_PATH=') else l) for l in lines]
p.write_text('\n'.join(lines).rstrip()+'\n')
PY
else
  printf '\nOBSIDIAN_VAULT_PATH=/root/ObsidianVault\n' >> /root/.hermes/.env
fi

# 3) Verify no-agent watcher exists, fail loudly if not
WATCHER_PRESENT=$(hermes cron list 2>/dev/null | grep -c 'obsidian-danny-task-board-alert' || true)
if [ "$WATCHER_PRESENT" = "0" ]; then
  echo "WARNING: obsidian-danny-task-board-alert not found. Recreate via Hermes cron tool."
else
  echo "Watcher present: obsidian-danny-task-board-alert"
fi

# 4) Write self operating rules into vault
cat > "/root/ObsidianVault/Agents/Danny Operating Rules.md" <<'EOF'
# Danny Operating Rules

Derrick's non-negotiable requirement: reusable workflows must be saved as Hermes skills so he does not pay to reteach the same thing.

## Required behavior

1. Before work, load any relevant skill.
2. During work, if a reusable workflow is discovered, create or patch a skill immediately.
3. After complex work, verify whether a skill should be created or updated.
4. Notes are not enough. Obsidian is for project context. Hermes skills are for repeatable workflows.
5. Do not claim a setup is complete unless verified with a tool.
6. Do not describe future action when a tool can do it now.
7. Use proof: command output, file path, commit hash, preview URL, screenshot, or cron job ID.

## Current critical skills

- leadcurate-brand-landing-page
- obsidian-agent-bridge
- lead-data-product-planning
- hermes-agent

## Bridge truth

- Ella can give Danny tasks through `/root/ObsidianVault/Agents/Task Board.md`.
- The watcher is script-only/no-agent and should not burn model tokens.
- Direct SSH into Ella's laptop is not done until a reachable IP/tunnel and SSH credentials exist.
EOF

echo "== Danny self-repair complete =="
echo "Curator: $(hermes curator status 2>/dev/null | sed -n '1p' || true)"
echo "Vault: $(grep '^OBSIDIAN_VAULT_PATH=' /root/.hermes/.env)"
echo "Skills relevant:"
hermes skills list 2>/dev/null | grep -Ei 'leadcurate-brand-landing-page|obsidian-agent-bridge|lead-data-product-planning' || true
