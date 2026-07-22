#!/usr/bin/env python3
"""Compress Dollar Leads batch CSVs without changing their row content.

Every original file is SHA-256 checked against the inventory before it is
removed. The gzip copy is then decompressed and checked against the same hash.
The inventory and lane manifests are replaced atomically after all files pass.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO


DEFAULT_BATCH_ROOT = Path("/opt/leadcurate/dollar_batches")
CHUNK_SIZE = 1024 * 1024


def stream_sha256(handle: BinaryIO) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
        digest.update(chunk)
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return stream_sha256(handle)


def gzip_content_sha256(path: Path) -> str:
    with gzip.open(path, "rb") as handle:
        return stream_sha256(handle)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def compress_batch(entry: dict[str, Any], compresslevel: int) -> tuple[int, int, str]:
    source = Path(entry["file"])
    expected_content_hash = entry.get("content_sha256") or entry["sha256"]
    before_bytes = int(entry.get("uncompressed_bytes") or 0)
    if source.suffix == ".gz":
        compressed = source
        if not compressed.exists():
            raise FileNotFoundError(compressed)
    else:
        compressed = Path(f"{source}.gz")
        if source.exists():
            before_bytes = source.stat().st_size
            source_hash = file_sha256(source)
            if source_hash != expected_content_hash:
                raise ValueError(f"source SHA-256 mismatch: {source}")
            temporary = Path(f"{compressed}.tmp")
            temporary.unlink(missing_ok=True)
            try:
                with source.open("rb") as input_handle, temporary.open("wb") as raw_output:
                    with gzip.GzipFile(fileobj=raw_output, mode="wb", compresslevel=compresslevel, mtime=0) as output_handle:
                        shutil.copyfileobj(input_handle, output_handle, CHUNK_SIZE)
                    raw_output.flush()
                    os.fsync(raw_output.fileno())
                if gzip_content_sha256(temporary) != expected_content_hash:
                    raise ValueError(f"compressed content SHA-256 mismatch: {source}")
                temporary.replace(compressed)
                source.unlink()
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
        elif compressed.exists():
            if gzip_content_sha256(compressed) != expected_content_hash:
                raise ValueError(f"recovered gzip content SHA-256 mismatch: {compressed}")
        else:
            raise FileNotFoundError(f"missing batch and gzip copy: {source}")

    content_hash = gzip_content_sha256(compressed)
    if content_hash != expected_content_hash:
        raise ValueError(f"gzip content SHA-256 mismatch: {compressed}")
    if not before_bytes:
        # The original was already removed during this run or an earlier interrupted run.
        with gzip.open(compressed, "rb") as handle:
            before_bytes = sum(len(chunk) for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""))
    after_bytes = compressed.stat().st_size
    entry.update({
        "file": str(compressed),
        "sha256": file_sha256(compressed),
        "content_sha256": expected_content_hash,
        "compression": "gzip",
        "uncompressed_bytes": before_bytes,
        "compressed_bytes": after_bytes,
    })
    return before_bytes, after_bytes, content_hash


def main() -> int:
    parser = argparse.ArgumentParser(description="Losslessly compress live Dollar Leads batch CSV files")
    parser.add_argument("--cycle-slug", required=True)
    parser.add_argument("--batch-root", type=Path, default=DEFAULT_BATCH_ROOT)
    parser.add_argument("--market")
    parser.add_argument("--lane")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--compresslevel", type=int, choices=range(1, 10), default=6)
    args = parser.parse_args()

    inventory_path = args.batch_root / args.cycle_slug / "inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    selected: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for lane in inventory.get("lanes", []):
        if args.market and lane.get("market") != args.market:
            continue
        if args.lane and lane.get("lane") != args.lane:
            continue
        for batch in lane.get("batches", []):
            selected.append((lane, batch))
            if args.limit and len(selected) >= args.limit:
                break
        if args.limit and len(selected) >= args.limit:
            break
    if not selected:
        raise ValueError("no inventory batches matched the requested scope")

    before_total = 0
    after_total = 0
    records_total = 0
    verified_hashes = 0
    touched_lanes: dict[tuple[str, str], dict[str, Any]] = {}
    for index, (lane, batch) in enumerate(selected, start=1):
        before, after, _ = compress_batch(batch, args.compresslevel)
        before_total += before
        after_total += after
        records_total += int(batch["size"])
        verified_hashes += 1
        touched_lanes[(lane["market"], lane["lane"])] = lane
        if index % 250 == 0 or index == len(selected):
            print(f"verified_and_compressed={index}/{len(selected)}", flush=True)

    inventory["storage_format"] = "gzip-batches"
    inventory["storage_updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    atomic_json(inventory_path, inventory)
    for lane in touched_lanes.values():
        first_batch = lane.get("batches", [{}])[0]
        lane_path = Path(first_batch["file"]).parent / "manifest.json"
        atomic_json(lane_path, lane)

    report = {
        "ok": True,
        "cycle_slug": args.cycle_slug,
        "market": args.market,
        "lane": args.lane,
        "batch_count": len(selected),
        "record_count": records_total,
        "content_hashes_verified": verified_hashes,
        "uncompressed_bytes": before_total,
        "compressed_bytes": after_total,
        "bytes_reclaimed": before_total - after_total,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    report_name = "storage-compression-verification.json" if not args.market and not args.lane and not args.limit else f"storage-compression-verification-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    atomic_json(inventory_path.parent / report_name, report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
