#!/usr/bin/env python3
"""Lane QA gate: run BEFORE any lane is sold, delivered, or marked live.

Catches the defect classes that reached production on 2026-07-24:
  1. Owner-occupied properties labeled as absentee/landlord
  2. Institutional owners (government, church, bank, school) in wholesale lanes
  3. Unaffordable outliers at the front of the file, where small packs read
  4. Missing core customer-facing fields

Exit code 0 = lane passes. Exit code 1 = lane FAILS, do not sell it.

Usage:
    python3 qa_lane_gate.py --market mecklenburg-nc --lane tired-landlords
    python3 qa_lane_gate.py --all                 # gate every lane in the cycle
    python3 qa_lane_gate.py --all --json          # machine-readable for agents
"""
from __future__ import annotations

import argparse
import csv
import glob
import gzip
import json
import os
import re
import sys
from pathlib import Path

# Applies to EVERY LeadCurate data product, not just Dollar Leads: premium
# territory deliveries, white-label client instances, sample deliveries, and
# any new market. Point --root at whatever tree holds the lane files.
DEFAULT_ROOT = Path("/opt/leadcurate/dollar_batches/2026-07")
CYCLE_ROOT = DEFAULT_ROOT  # rebound from --root at runtime
csv.field_size_limit(2**31 - 1)

# A lane whose whole premise is "the owner does not live there".
ABSENTEE_LANES = {
    "tired-landlords",
    "absentee-owners",
    "high-value-absentee",
    "out-of-state-owners",
}

# Lanes sold to wholesalers, where institutional owners are noise.
WHOLESALE_LANES = ABSENTEE_LANES | {
    "verified-vacant-land",
    "code-violations",
    "tax-debt",
    "live-tax-debt",
    "property-liens",
    "city-liens",
    "individual-homeowner",
    "high-equity",
}

MAX_OWNER_OCCUPIED_PCT = 2.0     # Dallas achieves 0.1%; 2% is the ceiling
MAX_INSTITUTIONAL_PCT = 1.0
MAX_FRONT_OUTLIER_PCT = 20.0     # of the first 50 records (a $5 pack)

INSTITUTIONAL = re.compile(
    r"\b(DEPT|DEPARTMENT|CITY OF|COUNTY OF|STATE OF|SCHOOL|CHURCH|DIOCESE|BISHOP"
    r"|UNIVERSITY|COLLEGE|HOSPITAL|HEALTHCARE|AUTHORITY|COMMISSION|TRANSPORTATION"
    r"|HOUSING AUTHORITY|MUNICIPAL|TOWN OF|VILLAGE OF|CEMETERY|FOUNDATION"
    r"|MINISTR|BAPTIST|METHODIST|PRESBYTER|SYNAGOGUE|MOSQUE|REDEVELOPMENT"
    r"|PARK DISTRICT|SANITAR|WATER DIST|FIRE DIST|LIBRARY)\b"
)

STREET_SUFFIXES = {
    "ST", "STREET", "AVE", "AV", "AVENUE", "RD", "ROAD", "DR", "DRIVE",
    "LN", "LANE", "CT", "COURT", "BLVD", "BOULEVARD", "HWY", "HY", "HIGHWAY",
    "PL", "PLACE", "CIR", "CIRCLE", "WAY", "TER", "TERRACE", "PKWY", "PARKWAY",
    "TRL", "TRAIL", "LOOP", "RUN", "PT", "POINT", "SQ", "SQUARE",
}

# Field names differ per market/lane; check every known alias.
OWNER_FIELDS = ("lc_owner_name", "owner_name", "OWNER1", "Owner_LastName", "COMM_OWNER")
PROP_FIELDS = ("lc_property_address", "property_address", "SITE_ADDR",
               "ADDR_PROP_ADDRESS_FULL", "Property_Address", "property_street")
MAIL_FIELDS = ("lc_mailing_address", "mailing_address", "Mailing_Address",
               "ADDR_MAIL_ADDRESS_FULL", "OWN_ADDR", "owner_street")

# Some counties publish addresses split across component columns rather than
# one readable field (Shelby TN is the clearest case). Reassemble before
# judging coverage, otherwise the gate reports a false hole in the data.
PROP_COMPOSITES = (
    ("PAR_ADRNO", "PAR_ADRPREDIR", "PAR_ADRSTR", "PAR_ADRSUF"),
    ("STREET_NUM", "FULL_STREET_NAME"),
    ("ADDR_NUM", "FULL_STR"),
)
MAIL_COMPOSITES = (
    ("OWN_ADRNO", "OWN_ADRPREDIR", "OWN_ADRSTR", "OWN_ADRSUF"),
    ("OWNER_ADDRESS_LINE1", "OWNER_ADDRESS_LINE2"),
)


def composite_value(row: dict, groups: tuple) -> str:
    for group in groups:
        parts = [(row.get(c) or "").strip() for c in group]
        if any(parts):
            return " ".join(p for p in parts if p)
    return ""
PARCEL_FIELDS = ("lc_parcel_id", "parcel_id", "parcel_pid", "parcel_key",
                 "Tax_ID", "PID", "U_PIN")
VALUE_FIELDS = ("total_value", "Total_Value", "lc_total_value", "assessed_value",
                "VAL_MAILED_TOT", "TOTAL_VAL", "land_value", "Land_Value")


def first_value(row: dict, names: tuple) -> str:
    for n in names:
        v = (row.get(n) or "").strip()
        if v:
            return v
    return ""


def property_key(value: str) -> str:
    """House number + first real street word. Immune to city/state/ZIP noise,
    duplicated city suffixes, and STREET vs ST style differences."""
    s = re.sub(r"[^A-Z0-9 ]", " ", (value or "").upper())
    tokens = s.split()
    if not tokens:
        return ""
    number = next((t for t in tokens if t.isdigit()), "")
    if not number:
        return ""
    idx = tokens.index(number)
    for token in tokens[idx + 1:]:
        if token in ("N", "S", "E", "W"):
            continue
        if token in STREET_SUFFIXES or token.isdigit():
            break
        return f"{number}|{token}"
    return f"{number}|"


def is_po_box(value: str) -> bool:
    return bool(re.search(r"\bP\s*\.?\s*O\.?\s*BOX\b|\bPOBOX\b", (value or "").upper()))


def read_rows(lane_dir: Path, max_batches: int):
    """Dollar Leads uses batch-00001.csv.gz; premium and white-label deliveries
    under /opt/leadcurate/processed use <market>-<lane>-<date>.csv. Support both,
    and never treat a preview or meta file as the deliverable."""
    files = sorted(glob.glob(str(lane_dir / "batch-*.csv*")))[:max_batches]
    if not files:
        files = [
            p for p in sorted(glob.glob(str(lane_dir / "*.csv*")))
            if "preview" not in os.path.basename(p) and "meta" not in os.path.basename(p)
        ][:max_batches]
    rows = []
    for path in files:
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
            rows.extend(list(csv.DictReader(handle)))
    return rows, len(files)


def to_float(value: str):
    try:
        return float(re.sub(r"[^0-9.\-]", "", value or "") or 0)
    except ValueError:
        return 0.0


def gate_lane(market: str, lane: str, max_batches: int = 6) -> dict:
    lane_dir = CYCLE_ROOT / market / lane
    result = {"market": market, "lane": lane, "passed": True, "failures": [], "warnings": {}}

    if not lane_dir.is_dir():
        result.update(passed=False, failures=["lane directory not found"])
        return result

    rows, batch_count = read_rows(lane_dir, max_batches)
    if not rows:
        result.update(passed=False, failures=["no readable batch rows"])
        return result

    result["batches_sampled"] = batch_count
    result["rows_sampled"] = len(rows)

    # 1. Core field coverage, counting split-column addresses as present
    def prop_addr(row):
        return first_value(row, PROP_FIELDS) or composite_value(row, PROP_COMPOSITES)

    def mail_addr(row):
        return first_value(row, MAIL_FIELDS) or composite_value(row, MAIL_COMPOSITES)

    for label, getter in (("owner", lambda r: first_value(r, OWNER_FIELDS)),
                          ("property_address", prop_addr),
                          ("parcel_id", lambda r: first_value(r, PARCEL_FIELDS))):
        filled = sum(1 for r in rows if getter(r))
        pct = round(filled / len(rows) * 100, 1)
        result["warnings"][f"{label}_populated_pct"] = pct
        if pct < 95.0:
            result["passed"] = False
            result["failures"].append(f"{label} populated on only {pct}% of rows")

    # 2. Owner-occupancy, the defect that reached production
    if lane in ABSENTEE_LANES:
        same = comparable = 0
        for row in rows:
            mail_raw = mail_addr(row)
            if is_po_box(mail_raw):
                comparable += 1
                continue
            p = property_key(prop_addr(row))
            m = property_key(mail_raw)
            if not p or not m:
                continue
            comparable += 1
            if p == m:
                same += 1
        if comparable:
            pct = round(same / comparable * 100, 1)
            result["warnings"]["owner_occupied_pct"] = pct
            if pct > MAX_OWNER_OCCUPIED_PCT:
                result["passed"] = False
                result["failures"].append(
                    f"{pct}% of rows are owner-occupied, ceiling is {MAX_OWNER_OCCUPIED_PCT}%"
                )

    # 3. Institutional owners in wholesale lanes
    if lane in WHOLESALE_LANES:
        hits = sum(1 for r in rows if INSTITUTIONAL.search(first_value(r, OWNER_FIELDS).upper()))
        pct = round(hits / len(rows) * 100, 1)
        result["warnings"]["institutional_pct"] = pct
        if pct > MAX_INSTITUTIONAL_PCT:
            result["passed"] = False
            result["failures"].append(
                f"{pct}% institutional owners, ceiling is {MAX_INSTITUTIONAL_PCT}%"
            )

    # 4. Front-of-file affordability, what a $5 pack actually receives
    values = [to_float(first_value(r, VALUE_FIELDS)) for r in rows]
    usable = [v for v in values if v > 0]
    if len(usable) >= 100:
        usable_sorted = sorted(usable)
        median = usable_sorted[len(usable_sorted) // 2]
        ceiling = median * 10
        front = [v for v in values[:50] if v > 0]
        if front:
            outliers = sum(1 for v in front if v > ceiling)
            pct = round(outliers / len(front) * 100, 1)
            result["warnings"]["median_value"] = int(median)
            result["warnings"]["front50_outlier_pct"] = pct
            if pct > MAX_FRONT_OUTLIER_PCT:
                result["passed"] = False
                result["failures"].append(
                    f"{pct}% of the first 50 records exceed 10x the lane median "
                    f"(${int(median):,}); small packs would get unusable data"
                )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market")
    parser.add_argument("--lane")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--batches", type=int, default=6)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help="Tree holding market/lane folders. Use "
                             "/opt/leadcurate/processed/<market> style trees to gate "
                             "premium and white-label deliveries, not just Dollar Leads.")
    args = parser.parse_args()

    global CYCLE_ROOT
    CYCLE_ROOT = args.root
    if not CYCLE_ROOT.is_dir():
        print(f"root not found: {CYCLE_ROOT}", file=sys.stderr)
        return 1

    targets = []
    if args.all:
        for market_dir in sorted(p for p in CYCLE_ROOT.iterdir() if p.is_dir()):
            for sub in sorted(p for p in market_dir.iterdir() if p.is_dir()):
                # processed/<market>/<date>/<lane>: descend the date level so the
                # premium and white-label trees gate the same as Dollar Leads.
                nested = sorted(p for p in sub.iterdir() if p.is_dir())
                if nested and not glob.glob(str(sub / "*.csv*")):
                    for lane_dir in nested:
                        targets.append((market_dir.name, f"{sub.name}/{lane_dir.name}"))
                else:
                    targets.append((market_dir.name, sub.name))
    elif args.market and args.lane:
        targets.append((args.market, args.lane))
    else:
        parser.error("provide --market and --lane, or --all")

    results = [gate_lane(m, l, args.batches) for m, l in targets]
    failed = [r for r in results if not r["passed"]]

    if args.json:
        print(json.dumps({"total": len(results), "failed": len(failed), "results": results}, indent=2))
    else:
        for r in results:
            if r["passed"]:
                w = r.get("warnings", {})
                extra = []
                if "owner_occupied_pct" in w:
                    extra.append(f"owner-occupied {w['owner_occupied_pct']}%")
                if "institutional_pct" in w:
                    extra.append(f"institutional {w['institutional_pct']}%")
                print(f"PASS  {r['market']:26s} {r['lane']:28s} " + "  ".join(extra))
            else:
                print(f"FAIL  {r['market']:26s} {r['lane']:28s}")
                for f in r["failures"]:
                    print(f"        -> {f}")
        print(f"\n{len(results) - len(failed)} passed, {len(failed)} FAILED")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
