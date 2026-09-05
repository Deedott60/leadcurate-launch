#!/usr/bin/env python3
from pathlib import Path
import argparse, csv, re

parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()
src = Path("/opt/leadcurate/raw_imports/mecklenburg-nc/parcel-lookup.csv")
if not src.exists():
    raise SystemExit("Mecklenburg parcel lookup source missing")
out = Path(args.output_dir) / "mecklenburg-probate.csv"
count = 0
with src.open(newline="", encoding="utf-8-sig", errors="replace") as fh, out.open("w", newline="", encoding="utf-8") as oh:
    reader = csv.DictReader(fh)
    fields = reader.fieldnames or []
    writer = csv.DictWriter(oh, fieldnames=fields + ["probate_signal"])
    writer.writeheader()
    for row in reader:
        owner = f"{row.get('Owner_FirstName','')} {row.get('Owner_LastName','')}"
        deed = row.get("TypeOfDeed", "")
        if re.search(r"\b(heir|estate|hrs|deceased|executor|admin)\b", owner + " " + deed, re.I):
            row["probate_signal"] = "owner/deed probate keyword"
            writer.writerow(row)
            count += 1
print(f"wrote {count} probate candidates to {out}")
