"""
LeadCurate 4-Tier Classifier
-----------------------------
Tags every record in a snapshot CSV with one of four tiers:
  Tier 1 — Hot Sheet      (auction <= 30 days)
  Tier 2 — Fresh Trigger  (record new vs prior pull)
  Tier 3 — Breaking Point (debt > 5% assessed value OR YoY growth)
  Tier 4 — Deep Distress  (default — base source category)

Usage:
  python tier_classifier.py <snapshot.csv> [--prior <prior_pull.csv>] [--out <output.csv>]

Inputs expected on the row (column names auto-detected, case-insensitive):
  - parcel_id        (required — used as unique key)
  - delinquent_amount or balance or amount_owed
  - assessed_value or market_value (optional — needed for Breaking Point)
  - auction_date or sale_date     (optional — needed for Hot Sheet)
  - score                          (existing distress score)

Outputs the same CSV with three new columns:
  - tier             ("Hot Sheet" / "Fresh Trigger" / "Breaking Point" / "Deep Distress")
  - tier_score       (adjusted 0-100 score after tier rules)
  - tier_reason      (why this tier was assigned)
"""

from __future__ import annotations
import argparse, csv, sys
from datetime import date, datetime
from pathlib import Path

csv.field_size_limit(sys.maxsize)


def find_col(headers: list[str], *candidates: str) -> str | None:
    lower = {h.lower(): h for h in headers}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def parse_float(v) -> float:
    if v is None or v == "":
        return 0.0
    try:
        return float(str(v).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def parse_date(v) -> date | None:
    if not v:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(v).strip(), fmt).date()
        except ValueError:
            continue
    return None


def classify(row: dict, cols: dict, prior_keys: set[str]) -> tuple[str, int, str]:
    """Returns (tier_name, tier_score, reason)."""
    base_score = int(parse_float(row.get(cols.get("score") or "", 50)))
    parcel = (row.get(cols["parcel"]) or "").strip()
    debt = parse_float(row.get(cols.get("debt") or ""))
    assessed = parse_float(row.get(cols.get("assessed") or ""))
    auction = parse_date(row.get(cols.get("auction") or ""))

    # TIER 1 — Hot Sheet (auction proximity)
    if auction:
        days_to = (auction - date.today()).days
        if 0 <= days_to < 14:
            return ("Hot Sheet", 99, f"Auction in {days_to} days")
        if 14 <= days_to < 30:
            return ("Hot Sheet", 95, f"Auction in {days_to} days")
        if 30 <= days_to < 60:
            return ("Breaking Point", min(100, base_score + 25),
                    f"Auction in {days_to} days (approaching)")

    # TIER 2 — Fresh Trigger (record new vs prior pull)
    if prior_keys and parcel and parcel not in prior_keys:
        return ("Fresh Trigger", 92, "New record vs prior pull")

    # TIER 3 — Breaking Point (debt-to-value or snowballing)
    if assessed > 0 and debt > 0:
        ratio = debt / assessed
        if ratio > 0.05:
            return ("Breaking Point", min(100, base_score + 20),
                    f"Debt {ratio*100:.1f}% of assessed value")

    # TIER 4 — Deep Distress (default)
    return ("Deep Distress", base_score, "Standard distress profile")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot", help="Path to current snapshot CSV")
    ap.add_argument("--prior", help="Optional path to prior-pull CSV for Fresh Trigger detection")
    ap.add_argument("--out", help="Output path (default: <snapshot>_tiered.csv)")
    args = ap.parse_args()

    snap_path = Path(args.snapshot)
    out_path = Path(args.out) if args.out else snap_path.with_name(snap_path.stem + "_tiered.csv")

    # Load prior pull keys (parcel IDs)
    prior_keys: set[str] = set()
    if args.prior:
        prior_path = Path(args.prior)
        if prior_path.exists():
            with open(prior_path, encoding="utf-8") as fp:
                reader = csv.DictReader(fp)
                parcel_col = find_col(reader.fieldnames or [], "parcel_id", "parcel", "apn")
                if parcel_col:
                    prior_keys = {(r.get(parcel_col) or "").strip()
                                  for r in reader if (r.get(parcel_col) or "").strip()}
            print(f"  Loaded {len(prior_keys):,} prior-pull parcel IDs", file=sys.stderr)

    with open(snap_path, encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        headers = reader.fieldnames or []
        cols = {
            "parcel":   find_col(headers, "parcel_id", "parcel", "apn"),
            "debt":     find_col(headers, "delinquent_amount", "balance", "amount_owed", "tax_due"),
            "assessed": find_col(headers, "assessed_value", "market_value", "appraised_value"),
            "auction":  find_col(headers, "auction_date", "sale_date", "tax_sale_date"),
            "score":    find_col(headers, "score", "distress_score"),
        }
        if not cols["parcel"]:
            print(f"FATAL: no parcel_id column found in {snap_path}", file=sys.stderr)
            sys.exit(1)
        print(f"  Detected columns: {cols}", file=sys.stderr)

        out_fields = headers + ["tier", "tier_score", "tier_reason"]
        rows_out = []
        counts = {"Hot Sheet": 0, "Fresh Trigger": 0, "Breaking Point": 0, "Deep Distress": 0}
        for row in reader:
            tier, t_score, reason = classify(row, cols, prior_keys)
            row["tier"] = tier
            row["tier_score"] = t_score
            row["tier_reason"] = reason
            counts[tier] += 1
            rows_out.append(row)

    # Sort: tier priority, then tier_score desc
    tier_order = {"Hot Sheet": 0, "Fresh Trigger": 1, "Breaking Point": 2, "Deep Distress": 3}
    rows_out.sort(key=lambda r: (tier_order[r["tier"]], -int(r["tier_score"])))

    with open(out_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"\n  Wrote {len(rows_out):,} rows to {out_path}", file=sys.stderr)
    print(f"  Tier breakdown:", file=sys.stderr)
    for tier, n in counts.items():
        pct = (n / len(rows_out) * 100) if rows_out else 0
        print(f"    {tier:<18} {n:>6,}  ({pct:5.1f}%)", file=sys.stderr)


if __name__ == "__main__":
    main()
