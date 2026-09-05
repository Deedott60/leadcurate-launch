#!/usr/bin/env python3
"""Cobb GA PDF v2 — uses extract_text + structured row parsing instead of extract_tables."""
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
    r"VENTURE|EQUITY|CAPITAL|SFR|REI|HOMES?|ESTATE|LIVING)\b", re.IGNORECASE)

MONEY = re.compile(r"\$?\s*([\d,]+\.\d{2})")
PARCEL_PATTERN = re.compile(r"^(\d{11})\s")

# Pages are formatted like:
# Parcel ID    Owner Name                                Address                              Amount Each Bill  Prior Year
# 16004400560  SMITH JOHN A                              123 OAK ST                           $1,234.56         No
# (data row per line, possibly multi-line owner)

rows = []
debug_pages = []

print(f"Reading {PDF}", file=sys.stderr)
with pdfplumber.open(str(PDF)) as pdf:
    for page_num, page in enumerate(pdf.pages):
        if page_num and page_num % 50 == 0:
            print(f"  page {page_num}/{len(pdf.pages)}, {len(rows)} rows", file=sys.stderr)
        text = page.extract_text() or ""
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip headers/footers
            if line.lower().startswith(("parcel id", "page ", "cobb county", "delinquent tax")):
                continue
            # Need a parcel ID at the start AND a $ amount
            parcel_m = PARCEL_PATTERN.match(line)
            money_m = MONEY.search(line)
            if not parcel_m or not money_m:
                continue

            parcel = parcel_m.group(1)
            # Find all monetary amounts in line, take last one as the "amount each bill"
            amounts = MONEY.findall(line)
            amount = float(amounts[-1].replace(",", "")) if amounts else 0.0

            # Strip parcel from start, strip $amount from end-area
            rest = line[len(parcel):].strip()
            # Find where amount starts and split
            amt_pos = rest.rfind(amounts[-1]) if amounts else len(rest)
            mid = rest[:amt_pos].strip()
            # Mid contains: Owner Name + Address (sometimes "Prior Year" Yes/No tail)
            # Try to detect double-space or known patterns to split owner vs address
            # Cobb typically: owner name in CAPS, then street starts with number
            # Split on first occurrence of a number that looks like a house number followed by a space
            addr_m = re.search(r"\s+(\d{1,6}\s+[A-Z].*?)$", mid)
            if addr_m:
                owner = mid[:addr_m.start()].strip()
                addr = addr_m.group(1).strip()
            else:
                owner = mid
                addr = ""

            if not owner:
                continue

            # Detect "Yes" / "No" prior year tail
            prior = ""
            if line.rstrip().endswith(("Yes", "No")):
                prior = line.rstrip()[-3:].strip(" ")
                if prior not in ("Yes", "No"):
                    prior = ""

            rows.append({
                "parcel_id": parcel,
                "owner_name": owner.strip(),
                "site_addr": addr.strip(),
                "delinquent_amount": amount,
                "prior_year": prior,
            })

print(f"  total rows: {len(rows)}", file=sys.stderr)

# Score + classify
out = []
for r in rows:
    owner = r["owner_name"]
    is_entity = bool(ENTITY_PATTERNS.search(owner))
    amt = r["delinquent_amount"]
    score = 50
    if amt > 10000: score += 25
    elif amt > 5000: score += 18
    elif amt > 2500: score += 12
    elif amt > 1000: score += 6
    if is_entity: score += 8
    if r["prior_year"] == "Yes": score += 10
    out.append({
        "parcel_id": r["parcel_id"],
        "owner_name": owner,
        "owner_type": "entity" if is_entity else "individual",
        "site_addr": r["site_addr"],
        "delinquent_amount": amt,
        "prior_year_delinquent": r["prior_year"],
        "score": score,
    })

out.sort(key=lambda x: (x["score"], x["delinquent_amount"]), reverse=True)

csv_path = OUT_DIR / f"cobb-ga-delinquent-{date.today().isoformat()}.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as fp:
    if out:
        writer = csv.DictWriter(fp, fieldnames=list(out[0].keys()))
        writer.writeheader()
        writer.writerows(out)

# Redacted preview
def redact_name(n):
    parts = n.split()
    return " ".join((p[0] + "***") if len(p) > 1 else p for p in parts)

def redact_addr(a):
    return re.sub(r"\b\d+\b", "###", a, count=1)

preview_path = OUT_DIR / f"cobb-ga-delinquent-{date.today().isoformat()}-preview.csv"
with open(preview_path, "w", newline="", encoding="utf-8") as fp:
    if out:
        writer = csv.DictWriter(fp, fieldnames=list(out[0].keys()))
        writer.writeheader()
        for r in out[:25]:
            rr = dict(r)
            rr["owner_name"] = redact_name(rr["owner_name"])
            rr["site_addr"] = redact_addr(rr["site_addr"])
            writer.writerow(rr)

ent = sum(1 for r in out if r["owner_type"] == "entity")
total_value = sum(r["delinquent_amount"] for r in out)
multi_year = sum(1 for r in out if r["prior_year_delinquent"] == "Yes")
big_balance = sum(1 for r in out if r["delinquent_amount"] >= 5000)
meta = {
    "market": "Cobb County, GA (Atlanta NW metro)",
    "lane": "Tax Delinquent (active)",
    "pulled": "2026-06-20",
    "processed": date.today().isoformat(),
    "source": "Cobb Tax Commissioner Delinquent Tax List PDF, June 1 2026 cycle",
    "total_rows": len(out),
    "entity_count": ent,
    "individual_count": len(out) - ent,
    "multi_year_delinquent": multi_year,
    "high_balance_5k_plus": big_balance,
    "total_delinquent_value": int(total_value),
    "avg_delinquent_amount": int(total_value / max(1, len(out))),
    "min_score": out[-1]["score"] if out else 0,
    "max_score": out[0]["score"] if out else 0,
}
(OUT_DIR / "meta.json").write_text(json.dumps(meta, indent=2))

print(f"\n=== DONE ===", file=sys.stderr)
print(f"  CSV:     {csv_path}", file=sys.stderr)
print(f"  Preview: {preview_path}", file=sys.stderr)
print(json.dumps(meta, indent=2))
