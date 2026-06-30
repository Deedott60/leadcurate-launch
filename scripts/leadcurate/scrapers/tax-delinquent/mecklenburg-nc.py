#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil

parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()
src = Path("/opt/leadcurate/raw_imports/mecklenburg-nc/parcel-lookup.csv")
if not src.exists():
    raise SystemExit("Mecklenburg parcel lookup source missing")
dst = Path(args.output_dir) / "parcel-lookup.csv"
shutil.copy2(src, dst)
print(f"copied {dst}")
