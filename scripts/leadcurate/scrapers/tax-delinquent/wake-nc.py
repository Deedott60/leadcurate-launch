#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil

parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()
srcs = sorted(Path("/opt/leadcurate/raw_imports/wake-nc").glob("20*/delinquent*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
if not srcs:
    raise SystemExit("No Wake NC delinquent XLSX found")
dst = Path(args.output_dir) / srcs[0].name
shutil.copy2(srcs[0], dst)
print(f"copied {dst}")
