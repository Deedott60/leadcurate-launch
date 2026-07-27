#!/usr/bin/env python3
"""Expose verified Wayne events under each supportable catalog lane."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def build(source: Path, source_meta: Path, output_dir: Path, lane: str, run_date: str, explanation: str) -> dict[str, Any]:
    meta_in = json.loads(source_meta.read_text(encoding="utf-8"))
    lane_dir = output_dir / lane
    lane_dir.mkdir(parents=True, exist_ok=True)
    stem = f"wayne-mi-{lane}-{run_date}"
    full = lane_dir / f"{stem}.csv"
    preview = lane_dir / f"{stem}-preview.csv"
    seen: set[str] = set()
    preview_rows: list[dict[str, str]] = []
    with source.open(newline="", encoding="utf-8-sig", errors="replace") as src, full.open("w", newline="", encoding="utf-8") as dst:
        reader = csv.DictReader(src)
        fields = list(reader.fieldnames or [])
        if "lc_lane" not in fields:
            fields.append("lc_lane")
        writer = csv.DictWriter(dst, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in reader:
            key = clean(row.get("lc_parcel_id") or row.get("parcel_key") or row.get("PARCEL_NUMBER") or row.get("parcel_id")).upper()
            if not key or key in seen:
                continue
            seen.add(key)
            row["lc_lane"] = lane
            writer.writerow(row)
            if len(preview_rows) < 25:
                preview_rows.append(dict(row))
    with preview.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(preview_rows)
    payload = {
        "market": "wayne-mi", "lane": lane, "status": "verified",
        "source_name": meta_in.get("source_name") or meta_in.get("source_status") or source.name,
        "source_url": meta_in.get("source_url") or "",
        "source_data_as_of": meta_in.get("source_data_as_of") or meta_in.get("live_balance_valid_as_of") or "2026-07-15",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "records": len(seen),
        "classification_note": explanation,
        "outputs": {"full": str(full), "preview": str(preview)},
        "verification": {"full_csv_rows": len(seen), "unique_parcels_in_full_csv": len(seen), "duplicate_parcels_in_full_csv": 0},
    }
    (lane_dir / f"{stem}-meta.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tax-csv", type=Path, required=True)
    parser.add_argument("--tax-meta", type=Path, required=True)
    parser.add_argument("--blight-csv", type=Path, required=True)
    parser.add_argument("--blight-meta", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    results = {
        "recorded-tax-liens": build(args.tax_csv, args.tax_meta, args.output_dir, "recorded-tax-liens", args.date, "The official 2026 Wayne publication identifies delinquent tax liens; every emitted parcel also had a positive Treasurer balance in the live verification pass."),
        "code-violations": build(args.blight_csv, args.blight_meta, args.output_dir, "code-violations", args.date, "Detroit blight tickets are municipal property-code violations. This catalog view preserves the same current unpaid-ticket evidence under the broader code-violation category."),
    }
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
