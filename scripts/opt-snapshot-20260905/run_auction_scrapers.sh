#!/bin/bash
set -euo pipefail
LOG_DIR="/opt/leadcurate/logs"
mkdir -p "$LOG_DIR" /opt/leadcurate/snapshots/auction_calendars
LOG="$LOG_DIR/auction_scrapers_$(date -u +%Y%m%dT%H%M%SZ).log"
{
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting auction scrapers"
  python3.12 /opt/leadcurate/scripts/auction_scrapers/mecklenburg_auctions.py
  python3.12 /opt/leadcurate/scripts/auction_scrapers/fulton_auctions.py
  python3.12 /opt/leadcurate/scripts/auction_scrapers/wake_auctions.py
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Auction scrapers complete"
} >> "$LOG" 2>&1
