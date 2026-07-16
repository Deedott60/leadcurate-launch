#!/usr/bin/env python3
"""Verify every lane bundle in a processed market directory.

The verifier reads each final metadata file, streams its referenced full CSV,
checks parcel grain and file-matched counts, hashes the shipped file, and emits
one manifest that distinguishes verified, snapshot-only, and unavailable lanes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def clean(value: object) -> str:
    return str(value or "").strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parcel_key(row: dict[str, str]) -> str:
    raw = row.get("lc_parcel_id") or row.get("parcel_id") or row.get("map_number") or ""
    return "".join(character for character in clean(raw).upper() if character.isalnum())


def lane_status(source_status: str, records: int, valid: bool) -> str:
    normalized = source_status.lower()
    if "unavailable" in normalized and records == 0:
        return "unavailable"
    if "snapshot" in normalized and valid:
        return "verified_publication_snapshot"
    return "verified" if valid else "failed_verification"


def verify_meta(meta_path: Path) -> dict[str, object]:
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    outputs = metadata.get("outputs") or {}
    full = Path(outputs.get("full") or "")
    if not full.is_absolute():
        full = (meta_path.parent / full).resolve()
    if not full.is_file():
        return {
            "lane": metadata.get("lane") or meta_path.parent.name,
            "status": "failed_verification",
            "meta_file": str(meta_path),
            "full_file": str(full),
            "error": "Referenced full CSV does not exist",
        }
    rows = 0
    keys: set[str] = set()
    blank_keys = 0
    fields: list[str] = []
    with full.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        for row in reader:
            rows += 1
            key = parcel_key(row)
            if key:
                keys.add(key)
            else:
                blank_keys += 1
    duplicates = rows - len(keys) - blank_keys
    expected = int(metadata.get("records") or 0)
    source_status = clean(metadata.get("status"))
    source_url = metadata.get("source_url") or metadata.get("source_page")
    source_data_as_of = (
        metadata.get("source_data_as_of")
        or metadata.get("source_last_edit_at")
        or metadata.get("source_publication_dates")
    )
    source_complete = bool(source_url and source_data_as_of and source_status)
    valid = rows == expected and duplicates == 0 and blank_keys == 0 and source_complete
    if source_status.lower().startswith("unavailable") and rows == expected == 0:
        valid = True
    return {
        "market": metadata.get("market"),
        "lane": metadata.get("lane") or meta_path.parent.name,
        "status": lane_status(source_status, rows, valid),
        "source_status": source_status,
        "source_url": source_url,
        "source_data_as_of": source_data_as_of,
        "source_complete": source_complete,
        "retrieved_at": metadata.get("retrieved_at") or metadata.get("source_retrieved_at"),
        "limitation": metadata.get("current_status_limitation") or metadata.get("unavailable_reason"),
        "meta_file": str(meta_path),
        "full_file": str(full),
        "full_file_sha256": sha256(full),
        "field_count": len(fields),
        "meta_records": expected,
        "full_csv_rows": rows,
        "unique_parcels": len(keys),
        "blank_parcel_keys": blank_keys,
        "duplicate_parcels": duplicates,
        "meta_count_matches_file": rows == expected,
        "verification_passed": valid,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    meta_files = sorted(args.processed_dir.glob("*/*-meta.json"))
    if not meta_files:
        parser.error(f"No lane metadata files found under {args.processed_dir}")
    lanes = [verify_meta(path) for path in meta_files]
    payload = {
        "processed_dir": str(args.processed_dir),
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "lane_count": len(lanes),
        "lanes": lanes,
        "summary": {
            "verified": sum(item["status"] == "verified" for item in lanes),
            "verified_publication_snapshot": sum(
                item["status"] == "verified_publication_snapshot" for item in lanes
            ),
            "unavailable": sum(item["status"] == "unavailable" for item in lanes),
            "failed_verification": sum(item["status"] == "failed_verification" for item in lanes),
            "all_available_files_passed": all(item.get("verification_passed") for item in lanes),
            "total_full_csv_rows": sum(int(item.get("full_csv_rows") or 0) for item in lanes),
            "total_duplicate_parcels_within_lanes": sum(
                int(item.get("duplicate_parcels") or 0) for item in lanes
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["summary"]["failed_verification"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
