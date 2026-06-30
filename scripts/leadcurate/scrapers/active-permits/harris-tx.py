#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil

parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()
base = Path("/opt/leadcurate/raw_imports/harris-tx/2026-06-20")
for name in ["permits.txt", "owners.txt", "real_acct.txt"]:
    src = base / name
    if src.exists():
        shutil.copy2(src, Path(args.output_dir) / name)
print(f"copied Harris active permit files to {args.output_dir}")
