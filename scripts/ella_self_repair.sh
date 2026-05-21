#!/usr/bin/env bash
set -euo pipefail

echo "== Ella self-repair: starting =="

# 1) Basic paths
export OBSIDIAN_VAULT_PATH="${OBSIDIAN_VAULT_PATH:-/root/ObsidianVault}"
if [ -d "$HOME/ObsidianVault" ]; then
  export OBSIDIAN_VAULT_PATH="$HOME/ObsidianVault"
elif [ -d "/root/ObsidianVault" ]; then
  export OBSIDIAN_VAULT_PATH="/root/ObsidianVault"
else
  mkdir -p "$HOME/ObsidianVault/Agents" "$HOME/ObsidianVault/LeadCurate" "$HOME/ObsidianVault/Decisions"
  export OBSIDIAN_VAULT_PATH="$HOME/ObsidianVault"
fi
mkdir -p "$OBSIDIAN_VAULT_PATH/Agents" "$OBSIDIAN_VAULT_PATH/LeadCurate" "$OBSIDIAN_VAULT_PATH/Decisions"

# 2) Ensure Hermes env points to vault
mkdir -p "$HOME/.hermes"
touch "$HOME/.hermes/.env"
if grep -q '^OBSIDIAN_VAULT_PATH=' "$HOME/.hermes/.env"; then
  python3 - "$HOME/.hermes/.env" "$OBSIDIAN_VAULT_PATH" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vault=sys.argv[2]
lines=p.read_text().splitlines()
lines=[f'OBSIDIAN_VAULT_PATH={vault}' if l.startswith('OBSIDIAN_VAULT_PATH=') else l for l in lines]
p.write_text('\n'.join(lines).rstrip()+'\n')
PY
else
  printf '\nOBSIDIAN_VAULT_PATH=%s\n' "$OBSIDIAN_VAULT_PATH" >> "$HOME/.hermes/.env"
fi

# 3) Enable curator if Hermes CLI exists
if command -v hermes >/dev/null 2>&1; then
  hermes config set curator.enabled true >/dev/null 2>&1 || true
  hermes config set skills.auto_create_after_complex_tasks true >/dev/null 2>&1 || true
fi

# 4) Create/update task board
BOARD="$OBSIDIAN_VAULT_PATH/Agents/Task Board.md"
if [ ! -f "$BOARD" ]; then
cat > "$BOARD" <<'EOF'
# Agent Task Board

This is the bridge between Ella (local laptop Hermes) and Danny (VPS/Telegram Hermes).

## Danny Inbox

<!-- Ella: add Danny tasks below this line. -->


---
## Ella Inbox

<!-- Danny: add Ella tasks below this line. -->


---
## Results / Decisions

EOF
fi

# 5) Create local reusable workflow notes as backup/reference
cat > "$OBSIDIAN_VAULT_PATH/Agents/Ella Operating Rules.md" <<'EOF'
# Ella Operating Rules

Derrick's priority: do not waste tokens relearning solved workflows.

Rules:

1. If a workflow is repeatable, save it as a Hermes skill.
2. If a skill exists but is incomplete, patch it immediately.
3. Use Obsidian for shared notes/coordination.
4. Use GitHub for source of truth, commits, and proof.
5. Never claim work is pushed/done without proof: commit hash, file path, preview URL, screenshot, or command output.
6. For Danny tasks, write them to `Agents/Task Board.md` under Danny Inbox.

Current LeadCurate truth:
- Product is premium county-based property data, not generic leads.
- Keep trust-first, compliance-aware positioning.
- Contact data where available; DNC-aware fields where applicable.
- No guaranteed deals.
EOF

# 6) Output proof
cat <<EOF
== Ella self-repair complete ==
USER: $(whoami)
HOME: $HOME
OBSIDIAN_VAULT_PATH: $OBSIDIAN_VAULT_PATH
TASK_BOARD: $BOARD
HERMES_CONFIG: $(hermes config path 2>/dev/null || echo 'hermes not found')
HERMES_ENV: $(hermes config env-path 2>/dev/null || echo "$HOME/.hermes/.env")
CURATOR_STATUS:
$(hermes curator status 2>/dev/null | sed -n '1,12p' || echo 'hermes curator status unavailable')
EOF
