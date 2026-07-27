#!/usr/bin/env python3
"""Join Dallas County's current struck-off tax-foreclosure resale list to DCAD."""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pdfplumber


SOURCE_URL = "https://www.dallascounty.org/Assets/uploads/docs/public-works/StruckListWorking_2025_3-3-2026.pdf"


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def accounts_from_pdf(path: Path) -> tuple[set[str], dict[str, str]]:
    accounts: set[str] = set()
    context: dict[str, str] = {}
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").splitlines():
                for account in re.findall(r"\b\d{17}\b", line):
                    accounts.add(account)
                    context[account] = clean(line)
    return accounts, context


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    accounts, context = accounts_from_pdf(args.pdf)
    found: dict[str, dict[str, str]] = {}
    with args.canonical.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        source_fields = list(reader.fieldnames or [])
        for row in reader:
            account = clean(row.get("ACCOUNT_NUM"))
            if account in accounts:
                found[account] = row
    missing = sorted(accounts - found.keys())
    event_fields = ["lc_parcel_id", "lc_lane", "lc_event_status", "lc_source_url", "lc_source_row_text"]
    summaries: dict[str, Any] = {}
    for lane in ("tax-sale", "tax-debt"):
        rows = []
        for account in sorted(found):
            rows.append({
                **found[account],
                "lc_parcel_id": account,
                "lc_lane": lane,
                "lc_event_status": "Dallas County tax-foreclosure property held for sealed-bid resale; printed 2026-03-02",
                "lc_source_url": SOURCE_URL,
                "lc_source_row_text": context.get(account, ""),
            })
        lane_dir = args.output_dir / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        stem = f"dallas-tx-{lane}-{args.date}"
        fields = source_fields + event_fields
        for suffix, subset in (("", rows), ("-preview", rows[:25])):
            path = lane_dir / f"{stem}{suffix}.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                writer.writeheader(); writer.writerows(subset)
        payload = {
            "market": "dallas-tx", "lane": lane, "status": "verified",
            "source_name": "Dallas County Tax Foreclosure Properties for Resale by Dallas County",
            "source_url": SOURCE_URL, "source_data_as_of": "Printed 2026-03-02; list URL labeled 2026-03-03",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_accounts": len(accounts), "records": len(rows), "unmatched_accounts": missing,
            "outputs": {"full": str(lane_dir / f"{stem}.csv"), "preview": str(lane_dir / f"{stem}-preview.csv")},
            "verification": {"full_csv_rows": len(rows), "unique_parcels_in_full_csv": len(rows), "duplicate_parcels_in_full_csv": 0},
        }
        (lane_dir / f"{stem}-meta.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        summaries[lane] = payload
    print(json.dumps(summaries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
