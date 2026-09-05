#!/bin/bash
set -euo pipefail
LOG_DIR=/opt/leadcurate/logs
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/lead_scout_$(date -u +%Y%m%dT%H%M%SZ).log"
{
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Lead Scout start"
  python3 /opt/leadcurate/scripts/scout/reddit_scout.py || true
  # BiggerPockets watcher uses Playwright, which is installed for system python3.12 on this VPS.
  python3.12 /opt/leadcurate/scripts/scout/bp_scout.py || true
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Lead Scout done"
} >> "$LOG" 2>&1
