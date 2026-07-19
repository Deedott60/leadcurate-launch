#!/usr/bin/env python3
"""Cut new catalog lanes into pack-compatible, non-overlapping batches.

Existing market/lane directories and inventory entries are immutable. New
lanes use 500-row batches first, then a single 250/100/50 remainder batch when
possible. This keeps every listed batch fulfillable by at least one store pack
while never reusing a parcel within the lane.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROCESSED = Path("/opt/leadcurate/processed")
BATCH_ROOT = Path("/opt/leadcurate/dollar_batches")
CYCLE = "July 2026"
CYCLE_SLUG = "2026-07"
PACK_CHUNKS = (500, 250, 100, 50)

MARKETS = {
    "fulton-ga": "Fulton County GA (Atlanta)",
    "shelby-tn": "Shelby County TN (Memphis)",
    "dallas-tx": "Dallas County TX",
    "wayne-mi": "Wayne County MI",
    "cook-il": "Cook County IL",
    "massachusetts-statewide": "Massachusetts (statewide)",
    "mecklenburg-nc": "Mecklenburg County NC (Charlotte)",
}

LANES = {
    "tax-debt": "Live tax-debt owners",
    "recorded-tax-liens": "Recorded tax liens",
    "tax-sale": "Tax-sale properties",
    "pre-foreclosure": "Pre-foreclosure notices",
    "probate": "Probate / inherited properties",
    "code-violations": "Code-violation properties",
    "property-liens": "Municipal / property liens",
    "absentee-owners": "Absentee owners",
    "out-of-state-owners": "Out-of-state owners",
    "tired-landlords": "Long-hold landlords",
    "high-equity": "High-equity / high-value proxy",
    "individual-homeowner": "Individual homeowners",
    "entity-owned": "Entity / LLC-owned properties",
    "verified-vacant-land": "Vacant land",
    "active-permits": "Active permits / repair / demolition",
    "office": "Distressed office owners",
    "industrial": "Distressed industrial owners",
    "multifamily": "Distressed multifamily owners",
    "blight-pressure": "Blight-pressure properties",
}


def clean(value: Any) -> str:
    return " ".join(str(value or "").upper().split())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_for(market: str, lane: str, run_date: str) -> tuple[Path, dict[str, Any]] | None:
    candidates = [
        PROCESSED / market / run_date / lane / f"{market}-{lane}-{run_date}.csv",
        PROCESSED / market / run_date / "events" / lane / f"{market}-{lane}-{run_date}.csv",
    ]
    for path in candidates:
        if not path.exists():
            continue
        meta_path = path.with_name(f"{path.stem}-meta.json")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        if meta.get("status") in {"unavailable", "unavailable_from_current_source", "buildable-not-yet-built", "buildable-not-live", "stale-not-live"}:
            return None
        return path, meta
    return None


def key_fields(fields: list[str]) -> list[str]:
    preferred = ["lc_parcel_id", "parcel_id", "parcel_key", "ParcelID", "PARCELID", "ACCOUNT_NUM", "LC_PARCEL_KEY", "U_PIN", "PID"]
    return [field for field in preferred if field in fields]


def parcel_key(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        if value := clean(row.get(field)):
            return value
    return ""


def chunk_sizes(count: int) -> list[int]:
    sizes: list[int] = []
    remaining = count
    for size in PACK_CHUNKS:
        while remaining >= size:
            sizes.append(size)
            remaining -= size
    return sizes


def cut_lane(market: str, lane: str, source: Path, meta: dict[str, Any], destination: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    destination.mkdir(parents=True, exist_ok=False)
    spool = destination / ".eligible.csv"
    with source.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        keys = key_fields(fields)
        if not keys:
            raise ValueError(f"no parcel key field in {source}")
        seen: set[str] = set()
        duplicates = 0
        with spool.open("w", newline="", encoding="utf-8") as spool_handle:
            spool_writer = csv.DictWriter(spool_handle, fieldnames=fields)
            spool_writer.writeheader()
            for row in reader:
                key = parcel_key(row, keys)
                if not key:
                    continue
                if key in seen:
                    duplicates += 1
                    continue
                seen.add(key)
                spool_writer.writerow(row)
    eligible = len(seen)
    sizes = chunk_sizes(eligible)
    batches: list[dict[str, Any]] = []
    if not batches:
        if not sizes:
            spool.unlink(missing_ok=True)
            destination.rmdir()
            raise ValueError(f"{market}/{lane} has {eligible} rows, below the 50-record store minimum")
    with spool.open(newline="", encoding="utf-8") as spool_handle:
        reader = csv.DictReader(spool_handle)
        for batch_no, size in enumerate(sizes, 1):
            path = destination / f"batch-{batch_no:05d}.csv"
            first_key = last_key = ""
            written = 0
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for _ in range(size):
                    row = next(reader)
                    key = parcel_key(row, keys)
                    first_key = first_key or key
                    last_key = key
                    writer.writerow(row)
                    written += 1
            if written != size:
                raise RuntimeError(f"{market}/{lane} batch {batch_no}: wrote {written}, expected {size}")
            batches.append({
                "batch_no": batch_no,
                "size": size,
                "file": str(path),
                "sha256": sha256(path),
                "first_parcel_key": first_key,
                "last_parcel_key": last_key,
            })
    spool.unlink(missing_ok=True)
    offset = sum(sizes)
    manifest = {
        "market": market,
        "market_display": MARKETS[market],
        "lane": lane,
        "lane_display": LANES[lane],
        "source_name": meta.get("source_name") or meta.get("source_status") or meta.get("source_file") or source.name,
        "source_url": meta.get("source_url") or "",
        "source_file": str(source),
        "source_sha256": sha256(source),
        "pull_cycle": CYCLE,
        "eligible_records": eligible,
        "batch_count": len(batches),
        "batched_records": sum(item["size"] for item in batches),
        "remainder_records": eligible - offset,
        "parcel_key_fields": keys,
        "duplicate_parcel_keys": duplicates,
        "batch_sizes": {str(size): sum(1 for item in batches if item["size"] == size) for size in PACK_CHUNKS},
        "batches": batches,
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    db_rows = [{
        "market": market,
        "market_display": MARKETS[market],
        "lane": lane,
        "lane_display": LANES[lane],
        "batch_no": item["batch_no"],
        "size": item["size"],
        "seats_total": 3,
        "seats_sold": 0,
        "cycle": CYCLE,
        "status": "live",
    } for item in batches]
    return manifest, db_rows


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    pending = Path(name)
    try:
        pending.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        pending.replace(path)
    finally:
        pending.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--market", action="append", choices=sorted(MARKETS))
    parser.add_argument("--cycle-slug", default=CYCLE_SLUG)
    parser.add_argument(
        "--replace",
        action="append",
        default=[],
        metavar="MARKET/LANE",
        help="Back up and rebuild an unsold existing market/lane manifest entry.",
    )
    args = parser.parse_args()
    cycle_dir = BATCH_ROOT / args.cycle_slug
    inventory_path = cycle_dir / "inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    replace_pairs: set[tuple[str, str]] = set()
    for value in args.replace:
        try:
            market, lane = value.split("/", 1)
        except ValueError as exc:
            raise ValueError(f"invalid --replace value: {value}") from exc
        if market not in MARKETS or lane not in LANES:
            raise ValueError(f"unknown --replace market/lane: {value}")
        replace_pairs.add((market, lane))
    if replace_pairs:
        present = {(item["market"], item["lane"]) for item in inventory["lanes"]}
        missing = replace_pairs - present
        if missing:
            raise ValueError(f"cannot replace missing inventory lanes: {sorted(missing)}")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for market, lane in sorted(replace_pairs):
            current = cycle_dir / market / lane
            if current.exists():
                backup = BATCH_ROOT / "superseded" / stamp / args.cycle_slug / market / lane
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(current), str(backup))
        inventory["lanes"] = [
            item for item in inventory["lanes"]
            if (item["market"], item["lane"]) not in replace_pairs
        ]
    existing = {(item["market"], item["lane"]) for item in inventory["lanes"]}
    markets = args.market or list(MARKETS)
    new_manifests: list[dict[str, Any]] = []
    new_rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for market in markets:
        for lane in LANES:
            if (market, lane) in existing:
                continue
            located = source_for(market, lane, args.date)
            if not located:
                continue
            source, meta = located
            destination = cycle_dir / market / lane
            if destination.exists():
                raise FileExistsError(destination)
            try:
                manifest, rows = cut_lane(market, lane, source, meta, destination)
            except ValueError as exc:
                skipped.append({"market": market, "lane": lane, "reason": str(exc)})
                continue
            new_manifests.append(manifest)
            new_rows.extend(rows)
            existing.add((market, lane))
            print(f"{market}/{lane}: {manifest['eligible_records']} eligible -> {manifest['batch_count']} batches")
    inventory["lanes"].extend(new_manifests)
    inventory["lane_count"] = len(inventory["lanes"])
    inventory["batch_count"] = sum(int(item.get("batch_count", 0)) for item in inventory["lanes"])
    inventory["extended_at_utc"] = datetime.now(timezone.utc).isoformat()
    atomic_json(inventory_path, inventory)
    rows_path = cycle_dir / f"dollar_batches_rows_catalog_{args.date}.json"
    atomic_json(rows_path, new_rows)
    result = {"new_lanes": len(new_manifests), "new_batches": len(new_rows), "rows_file": str(rows_path), "skipped": skipped}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
