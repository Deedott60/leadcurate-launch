#!/usr/bin/env python3
"""Verify physical Dollar Leads batches against the authoritative inventory."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def clean(value: Any) -> str:
    return " ".join(str(value or "").upper().split())


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def parcel_key(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        if value := clean(row.get(field)):
            return value
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--market", action="append")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backfill-missing-sha256", action="store_true")
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    lanes = [item for item in inventory["lanes"] if not args.market or item["market"] in args.market]
    pairs = [(item["market"], item["lane"]) for item in lanes]
    if len(pairs) != len(set(pairs)):
        raise RuntimeError("inventory contains duplicate market/lane manifests")
    report_lanes: list[dict[str, Any]] = []
    repaired_lanes: set[tuple[str, str]] = set()
    for lane in lanes:
        keys = list(lane.get("parcel_key_fields") or [])
        if not keys:
            raise RuntimeError(f"{lane['market']}/{lane['lane']}: missing parcel-key fields")
        seen: set[str] = set()
        rows_total = 0
        for batch in lane["batches"]:
            path = Path(batch["file"])
            if not path.is_file():
                raise FileNotFoundError(path)
            stored = path.read_bytes()
            actual_digest = hashlib.sha256(stored).hexdigest()
            expected_digest = batch.get("sha256")
            if not expected_digest and args.backfill_missing_sha256:
                batch["sha256"] = actual_digest
                repaired_lanes.add((lane["market"], lane["lane"]))
            elif not expected_digest:
                raise RuntimeError(f"{path}: manifest has no SHA-256")
            elif actual_digest != expected_digest:
                raise RuntimeError(f"{path}: SHA-256 mismatch")
            raw = gzip.decompress(stored) if path.suffix == ".gz" else stored
            expected_content_digest = batch.get("content_sha256")
            if expected_content_digest and hashlib.sha256(raw).hexdigest() != expected_content_digest:
                raise RuntimeError(f"{path}: decompressed content SHA-256 mismatch")
            count = 0
            with io.StringIO(raw.decode("utf-8-sig", errors="replace"), newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    value = parcel_key(row, keys)
                    if not value:
                        raise RuntimeError(f"{path}: blank parcel key")
                    if value in seen:
                        raise RuntimeError(f"{lane['market']}/{lane['lane']}: overlapping parcel {value}")
                    seen.add(value)
                    count += 1
            if count != int(batch["size"]):
                raise RuntimeError(f"{path}: {count} rows, manifest says {batch['size']}")
            rows_total += count
        if len(lane["batches"]) != int(lane["batch_count"]) or rows_total != int(lane["batched_records"]):
            raise RuntimeError(f"{lane['market']}/{lane['lane']}: lane totals do not match batches")
        report_lanes.append({
            "market": lane["market"], "lane": lane["lane"], "batch_count": len(lane["batches"]),
            "batched_records": rows_total, "unique_parcel_keys": len(seen), "overlap_count": 0,
            "all_files_exist": True, "all_sha256_match": True, "all_row_counts_match": True,
        })
        print(f"verified {lane['market']}/{lane['lane']}: {len(lane['batches'])} batches, {rows_total} rows")
    if repaired_lanes:
        for lane in lanes:
            if (lane["market"], lane["lane"]) in repaired_lanes:
                lane_manifest = args.inventory.parent / lane["market"] / lane["lane"] / "manifest.json"
                lane_manifest.write_text(json.dumps(lane, indent=2) + "\n", encoding="utf-8")
        pending_inventory = args.inventory.with_name(f".{args.inventory.name}.hash-pending")
        pending_inventory.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
        pending_inventory.replace(args.inventory)
    payload = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "inventory": str(args.inventory), "market_filter": args.market,
        "lane_count": len(report_lanes), "batch_count": sum(row["batch_count"] for row in report_lanes),
        "batched_records": sum(row["batched_records"] for row in report_lanes),
        "checks": {"physical_files": "pass", "sha256": "pass", "row_counts": "pass", "within_lane_overlap": "pass"},
        "sha256_manifests_backfilled": [f"{market}/{lane}" for market, lane in sorted(repaired_lanes)],
        "lanes": report_lanes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("lane_count", "batch_count", "batched_records", "checks")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
