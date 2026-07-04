#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

RAW_ROOT = Path("/opt/leadcurate/raw_imports")


def clean(text: str) -> str:
    return " ".join(str(text or "").strip().split())


def money_parts(line: str) -> list[float]:
    return [float(m.group(0)) for m in re.finditer(r"\d+\.\d{2}", line)]


def receivables(zip_path: Path, max_lines: int) -> dict[str, float]:
    owed: dict[str, float] = defaultdict(float)
    with zipfile.ZipFile(zip_path) as zf, zf.open("Rec.DAT") as handle:
        for i, raw in enumerate(handle):
            if i >= max_lines:
                break
            line = raw.decode("latin1", errors="replace").rstrip("\r\n")
            account = clean(line[:11])
            amounts = [v for v in money_parts(line) if 0 < v < 1000000]
            if account and amounts:
                owed[account] += max(amounts)
    return owed


def master_rows(zip_path: Path, owed: dict[str, float], limit: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_path) as zf, zf.open("Master.dat") as handle:
        for raw in handle:
            line = raw.decode("latin1", errors="replace").rstrip("\r\n")
            account = clean(line[:11])
            total = owed.get(account, 0.0)
            if total <= 0:
                continue
            owner = clean(line[325:375])
            street = clean(line[375:425])
            city = clean(line[425:475])
            state = clean(line[475:478]) or "TX"
            zip_code = clean(line[496:505])
            if not owner or not street:
                continue
            rows.append({
                "parcel_id": account,
                "owner_name": owner,
                "address": street,
                "city": city or "Fort Worth",
                "Property ZIP": zip_code,
                "Mailing Street": street,
                "Mailing City": city,
                "Mailing State": state,
                "Mailing ZIP": zip_code,
                "total_owed": f"{total:.2f}",
                "value": "0",
                "source_url": str(zip_path),
            })
            if len(rows) >= limit:
                break
    return rows


def extract(zip_path: Path, output_dir: Path, limit: int, max_rec_lines: int) -> dict[str, object]:
    owed = receivables(zip_path, max_rec_lines)
    rows = master_rows(zip_path, owed, limit)
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "tax-roll-extracted.csv"
    fields = ["parcel_id", "owner_name", "address", "city", "Property ZIP", "Mailing Street", "Mailing City", "Mailing State", "Mailing ZIP", "total_owed", "value", "source_url"]
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return {"ok": True, "zip": str(zip_path), "rows": len(rows), "accounts_with_receivables": len(owed), "csv": str(out)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", default=str(RAW_ROOT / "tarrant-tx" / "2026-06-18" / "tax-roll.zip"))
    parser.add_argument("--output-dir", default=str(RAW_ROOT / "tarrant-tx" / date.today().isoformat()))
    parser.add_argument("--limit", type=int, default=10000)
    parser.add_argument("--max-rec-lines", type=int, default=500000)
    args = parser.parse_args()
    print(json.dumps(extract(Path(args.zip), Path(args.output_dir), args.limit, args.max_rec_lines), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
