#!/usr/bin/env python3
"""Publish the verified Charlotte municipal-lien join under the catalog lane."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-meta", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    source_meta = json.loads(args.source_meta.read_text(encoding="utf-8"))
    with args.source.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if "parcel_id" not in fields:
        raise ValueError("verified municipal-lien file has no parcel_id")
    seen: set[str] = set()
    output_rows: list[dict[str, str]] = []
    for row in rows:
        parcel = "".join(str(row.get("parcel_id") or "").upper().split())
        if not parcel or parcel in seen:
            continue
        seen.add(parcel)
        row["lane"] = "property-liens"
        output_rows.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"mecklenburg-nc-property-liens-{args.date}"
    full = args.output_dir / f"{stem}.csv"
    preview = args.output_dir / f"{stem}-preview.csv"
    for path, subset in ((full, output_rows), (preview, output_rows[:25])):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(subset)

    payload = {
        "market": "mecklenburg-nc",
        "lane": "property-liens",
        "status": "verified",
        "source_name": source_meta.get("source_name"),
        "source_url": source_meta.get("source_url"),
        "parcel_source_url": source_meta.get("parcel_source_url"),
        "source_data_as_of": args.date,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": len(output_rows),
        "policy": "Open Charlotte municipal liens joined to one current Mecklenburg parcel per parcel ID.",
        "verification": {
            "full_csv_rows": len(output_rows),
            "unique_parcels_in_full_csv": len(seen),
            "duplicate_parcels_in_full_csv": 0,
        },
        "outputs": {"full": str(full), "preview": str(preview)},
    }
    (args.output_dir / f"{stem}-meta.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
