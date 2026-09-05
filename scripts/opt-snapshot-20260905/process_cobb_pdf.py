#!/usr/bin/env python3
"""Cobb GA — Delinquent Tax List PDF → CSV snapshot."""
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber", "--break-system-packages", "-q"])
    import pdfplumber

PDF = Path("/opt/leadcurate/raw_imports/cobb-ga/2026-06-20/Cobb-Delinquent-Tax-List-06.01.2026.pdf")
OUT_DIR = Path("/opt/leadcurate/snapshots/cobb-ga") / date.today().isoformat()
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENTITY_PATTERNS = re.compile(
    r"\b(LLC|L\.L\.C\.|INC|CORP|CORPORATION|CO|COMPANY|LP|LTD|TRUST|TRUSTEE|"
    r"REIT|HOLDINGS?|PARTNERS?|GROUP|ASSOC|ASSN|FOUNDATION|FUND|CHURCH|"
    r"HOA|REALTY|PROPERTIES|INVESTMENTS?|RENTALS?|MGT|MGMT|"
    r"VENTURE|EQUITY|CAPITAL|SFR|REI|HOMES?)\b", re.IGNORECASE)

print(f"Reading PDF: {PDF}", file=sys.stderr)
all_rows = []
header = None
with pdfplumber.open(str(PDF)) as pdf:
    print(f"  pages: {len(pdf.pages)}", file=sys.stderr)
    for i, page in enumerate(pdf.pages):
        if i and i % 25 == 0:
            print(f"  …processed {i} pages, {len(all_rows)} rows so far", file=sys.stderr)
        tables = page.extract_tables()
        for tbl in tables:
            if not tbl:
                continue
            for row in tbl:
                # Strip cells
                cleaned = [(c or "").strip().replace("\n", " ") for c in row]
                if not any(cleaned):
                    continue
                # First non-empty row of first table = header
                if header is None and any(
                    h.lower() in " ".join(cleaned).lower()
                    for h in ("parcel", "owner", "amount", "tax")
                ):
                    header = cleaned
                    continue
                if header and len(cleaned) == len(header):
                    all_rows.append(cleaned)
                elif not header:
                    # Just take the row anyway if we haven't found a header
                    all_rows.append(cleaned)

print(f"  total rows extracted: {len(all_rows)}", file=sys.stderr)
print(f"  header detected: {header}", file=sys.stderr)
if not header and all_rows:
    # Synthesize header from typical Cobb format
    n = len(all_rows[0])
    header = [f"col_{i}" for i in range(n)]

# Build dict rows
dicts = []
for r in all_rows:
    if header and len(r) == len(header):
        dicts.append(dict(zip(header, r)))

# Detect columns
def find_col(header, *patterns):
    for h in header:
        for p in patterns:
            if p in h.lower():
                return h
    return None

if header:
    owner_col = find_col(header, "owner", "name")
    parcel_col = find_col(header, "parcel", "pin", "id")
    addr_col = find_col(header, "address", "situs", "location")
    amount_col = find_col(header, "amount", "due", "balance", "total")
    print(f"  owner={owner_col} parcel={parcel_col} addr={addr_col} amount={amount_col}", file=sys.stderr)

# Score and emit
def parse_amount(v):
    try:
        return float(re.sub(r"[^\d.]", "", str(v) or "0"))
    except Exception:
        return 0.0

rows_out = []
for d in dicts:
    owner = d.get(owner_col, "") if owner_col else ""
    if not owner:
        continue
    parcel = d.get(parcel_col, "") if parcel_col else ""
    addr = d.get(addr_col, "") if addr_col else ""
    amount = parse_amount(d.get(amount_col, "")) if amount_col else 0.0
    is_entity = bool(ENTITY_PATTERNS.search(owner))
    score = 50
    if amount > 5000: score += 20
    elif amount > 2500: score += 12
    elif amount > 1000: score += 6
    if is_entity: score += 8
    rows_out.append({
        "parcel_id": parcel,
        "owner_name": owner,
        "owner_type": "entity" if is_entity else "individual",
        "site_addr": addr,
        "delinquent_amount": amount,
        "score": score,
        **{k: v for k, v in d.items() if k not in (owner_col, parcel_col, addr_col, amount_col)},
    })

rows_out.sort(key=lambda r: (r["score"], r["delinquent_amount"]), reverse=True)

csv_path = OUT_DIR / f"cobb-ga-delinquent-{date.today().isoformat()}.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as fp:
    if not rows_out:
        print("  WARNING: no rows extracted", file=sys.stderr)
    else:
        writer = csv.DictWriter(fp, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)

ent = sum(1 for r in rows_out if r["owner_type"] == "entity")
meta = {
    "market": "Cobb County, GA (Atlanta NW)",
    "lane": "Tax Delinquent",
    "pulled": "2026-06-20",
    "processed": date.today().isoformat(),
    "source": "Cobb Tax Commissioner Delinquent Tax List PDF (06/01/2026 cycle)",
    "total_rows": len(rows_out),
    "entity_count": ent,
    "individual_count": len(rows_out) - ent,
    "total_delinquent_value": int(sum(r["delinquent_amount"] for r in rows_out)),
    "avg_delinquent_amount": int(sum(r["delinquent_amount"] for r in rows_out) / max(1, len(rows_out))),
    "header_detected": header,
}
(OUT_DIR / "meta.json").write_text(json.dumps(meta, indent=2))

print(f"\n=== DONE ===", file=sys.stderr)
print(f"  CSV:  {csv_path}", file=sys.stderr)
print(f"  Meta: {OUT_DIR / 'meta.json'}", file=sys.stderr)
print(json.dumps(meta, indent=2))
