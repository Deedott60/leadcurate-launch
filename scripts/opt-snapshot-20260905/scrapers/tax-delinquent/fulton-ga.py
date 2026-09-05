#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil

parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()
src = Path("/opt/leadcurate/raw_imports/fulton-ga/tax-parcels-2025.csv")
if not src.exists():
    raise SystemExit("Fulton GA tax parcel CSV missing")
dst = Path(args.output_dir) / "tax-parcels-2025.csv"
shutil.copy2(src, dst)
print(f"copied {dst}")
